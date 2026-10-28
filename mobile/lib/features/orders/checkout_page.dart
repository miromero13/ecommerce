import 'package:flutter/material.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../shared/widgets/qr_payment_dialog.dart';
import 'package:geolocator/geolocator.dart';
import 'package:flutter_stripe/flutter_stripe.dart' hide PaymentMethod;

import '../../core/config/app_config.dart';
import '../../app/routes.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_image.dart';
import '../../shared/widgets/product_price.dart';
import '../auth/auth_controller.dart';
import '../auth/login_dialog.dart';
import 'order_controller.dart';
import 'order_models.dart';

class CheckoutPage extends StatefulWidget {
  const CheckoutPage({
    super.key,
    required this.authController,
    this.orderId,
    this.controller,
  });

  final AuthController authController;
  final String? orderId;
  final OrderController? controller;

  @override
  State<CheckoutPage> createState() => _CheckoutPageState();
}

class _CheckoutPageState extends State<CheckoutPage> {
  late final OrderController _controller;
  late final bool _ownsController;
  String? _loadedToken;
  String? _pickupBranchId;
  // Web orders are always paid online (card or QR); cash only exists at the store's till.
  PaymentMethod _paymentMethod = PaymentMethod.qr;
  // CU20: in-store pickup or home delivery shipped from the selected branch.
  String _fulfillment = 'pickup';
  final _address = TextEditingController();
  final _reference = TextEditingController();
  final _latitude = TextEditingController();
  final _longitude = TextEditingController();
  final _points = TextEditingController(); // CU17: 10 points = 1 Bs
  Map<String, dynamic>? _quote;
  bool _quoting = false;

  bool get _isOrderPayment => widget.orderId != null;

  int get _pointsToRedeem => int.tryParse(_points.text.trim()) ?? 0;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller =
        widget.controller ??
        OrderController(authController: widget.authController);
    widget.authController.addListener(_handleAuthChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) => _handleAuthChanged());
  }

  @override
  void dispose() {
    widget.authController.removeListener(_handleAuthChanged);
    if (_ownsController) _controller.dispose();
    for (final c in [_address, _reference, _latitude, _longitude, _points]) {
      c.dispose();
    }
    super.dispose();
  }

  void _handleAuthChanged() {
    if (!mounted) return;
    if (!widget.authController.isAuthenticated) {
      _loadedToken = null;
      return;
    }
    final token = widget.authController.accessToken;
    if (token == null || token == _loadedToken) return;
    _loadedToken = token;
    _loadCheckout();
  }

  Future<void> _loadCheckout() async {
    await _controller.load();
    if (!mounted || widget.orderId == null) return;
    await _controller.loadDetail(widget.orderId!);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isOrderPayment ? 'Pagar pedido' : 'Finalizar compra'),
      ),
      body: ListenableBuilder(
        listenable: widget.authController,
        builder: (context, _) {
          if (widget.authController.status == AuthStatus.loading) {
            return const AppLoading(message: 'Validando sesión...');
          }
          if (widget.authController.status == AuthStatus.error) {
            return AppErrorView(
              message:
                  widget.authController.errorMessage ??
                  'No se pudo validar la sesión.',
              onRetry: widget.authController.restoreSession,
            );
          }
          if (!widget.authController.isAuthenticated) {
            return AppEmptyView(
              title: 'Pago privado',
              message: 'Inicia sesión para continuar con el pago.',
              actionLabel: 'Iniciar sesión',
              onAction: () => LoginDialog.show(
                context: context,
                controller: widget.authController,
              ),
            );
          }
          return ListenableBuilder(
            listenable: _controller,
            builder: (context, _) => _buildContent(context),
          );
        },
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    final order = _controller.selectedOrder;
    if (_controller.status == OrderControllerStatus.error &&
        (_isOrderPayment || _controller.orders.isEmpty)) {
      return AppErrorView(
        message: _controller.errorMessage ?? 'No se pudo cargar el pago.',
        onRetry: _loadCheckout,
      );
    }
    if (_controller.status == OrderControllerStatus.loading &&
        (_isOrderPayment && order == null ||
            !_isOrderPayment && _controller.orders.isEmpty)) {
      return const AppLoading(message: 'Cargando pago...');
    }
    if (_isOrderPayment && order == null) {
      return const AppErrorView(message: 'No se encontró el pedido.');
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      children: [
        if (_controller.status == OrderControllerStatus.loading)
          const LinearProgressIndicator(minHeight: 2),
        AppSectionTitle(
          title: _isOrderPayment ? 'Finalizar pedido' : 'Finalizar compra',
          subtitle: _isOrderPayment
              ? 'Completa el pago para continuar con la preparación.'
              : 'Elige dónde retirarás tu pedido y cómo pagarás.',
        ),
        const SizedBox(height: 16),
        if (order != null) ...[
          _OrderSummary(order: order),
          const SizedBox(height: 12),
        ],
        _checkoutCard(context),
      ],
    );
  }

  Widget _checkoutCard(BuildContext context) {
    final isSaving = _controller.status == OrderControllerStatus.saving;
    final branches = _controller.pickupBranches
        .where((branch) => branch.isActive)
        .toList(growable: false);
    final pickupBranchId = _selectedBranchId(branches);

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!_isOrderPayment) ...[
            DropdownButtonFormField<String>(
              isExpanded: true,
              initialValue: pickupBranchId,
              decoration: const InputDecoration(
                labelText: 'Sucursal de retiro',
              ),
              hint: const Text('Selecciona una sucursal'),
              items: branches
                  .map(
                    (branch) => DropdownMenuItem(
                      value: branch.id,
                      child: Text(
                        '${branch.name} · ${branch.city}',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  )
                  .toList(growable: false),
              onChanged: isSaving
                  ? null
                  : (value) => setState(() => _pickupBranchId = value),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _points,
              enabled: !isSaving,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Puntos a canjear (opcional)',
                helperText: '10 puntos = 1 Bs de descuento. Consulta tu saldo en Mis puntos.',
              ),
            ),
            const SizedBox(height: 12),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'pickup', label: Text('Retiro en tienda')),
                ButtonSegment(value: 'delivery', label: Text('Envío a domicilio')),
              ],
              selected: {_fulfillment},
              onSelectionChanged: isSaving
                  ? null
                  : (value) => setState(() {
                      _fulfillment = value.first;
                      _quote = null;
                    }),
            ),
            if (_fulfillment == 'delivery') ...[
              const SizedBox(height: 12),
              TextField(controller: _address, decoration: const InputDecoration(labelText: 'Dirección de entrega')),
              TextField(controller: _reference, decoration: const InputDecoration(labelText: 'Referencia (opcional)')),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _latitude,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                      decoration: const InputDecoration(labelText: 'Latitud'),
                      onChanged: (_) => setState(() => _quote = null),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _longitude,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                      decoration: const InputDecoration(labelText: 'Longitud'),
                      onChanged: (_) => setState(() => _quote = null),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: _quoting || pickupBranchId == null ? null : () => _useMyLocation(pickupBranchId),
                    icon: const Icon(Icons.my_location_outlined),
                    label: const Text('Usar mi ubicación'),
                  ),
                  OutlinedButton(
                    onPressed: _quoting || pickupBranchId == null ? null : () => _quoteDelivery(pickupBranchId),
                    child: Text(_quoting ? 'Calculando...' : 'Calcular envío'),
                  ),
                ],
              ),
              if (_quote != null)
                Text(
                  'Distancia ${_quote!['distance_km']} km · Envío ${_quote!['shipping_cost']} BOB · ~${_quote!['estimated_minutes']} min',
                ),
            ],
            const SizedBox(height: 12),
            DropdownButtonFormField<PaymentMethod>(
              isExpanded: true,
              initialValue: _paymentMethod,
              decoration: const InputDecoration(labelText: 'Método de pago'),
              items: const [
                DropdownMenuItem(
                  value: PaymentMethod.stripe,
                  child: Text('Tarjeta'),
                ),
                DropdownMenuItem(
                  value: PaymentMethod.qr,
                  child: Text('QR'),
                ),
              ],
              onChanged: isSaving
                  ? null
                  : (value) => setState(() => _paymentMethod = value!),
            ),
            const SizedBox(height: 12),
          ],
          AppButton(
            label: _isOrderPayment || _paymentMethod == PaymentMethod.stripe
                ? 'Pagar con tarjeta'
                : 'Generar código QR',
            icon: Icon(
              _isOrderPayment || _paymentMethod == PaymentMethod.stripe
                  ? Icons.credit_card_outlined
                  : Icons.qr_code_2_outlined,
            ),
            onPressed: isSaving || (!_isOrderPayment && pickupBranchId == null)
                ? null
                : () => _submit(pickupBranchId),
            isLoading: isSaving,
            expand: true,
          ),
        ],
      ),
    );
  }

  String? _selectedBranchId(List<PickupBranch> branches) {
    if (_pickupBranchId != null &&
        branches.any((branch) => branch.id == _pickupBranchId)) {
      return _pickupBranchId;
    }
    return branches.where((branch) => branch.isDefault).firstOrNull?.id ??
        branches.firstOrNull?.id;
  }

  Future<void> _submit(String? pickupBranchId) async {
    if (_isOrderPayment) {
      await _checkoutStripe();
      return;
    }
    if (pickupBranchId == null) return;
    final delivery = _deliveryPayload();
    if (_fulfillment == 'delivery' && delivery == null) {
      AppSnackBar.show(context, 'Ingresa la dirección y calcula el costo de envío.', tone: AppSnackBarTone.warning);
      return;
    }
    if (_paymentMethod == PaymentMethod.stripe) {
      await _checkoutStripe(pickupBranchId: pickupBranchId, delivery: delivery);
      return;
    }
    await _checkoutQr(pickupBranchId, delivery);
  }

  Map<String, dynamic>? _deliveryPayload() {
    if (_fulfillment != 'delivery' || _quote == null || _address.text.trim().length < 5) return null;
    return {
      'address': _address.text.trim(),
      'reference': _reference.text.trim().isEmpty ? null : _reference.text.trim(),
      'latitude': double.parse(_latitude.text.trim()),
      'longitude': double.parse(_longitude.text.trim()),
    };
  }

  /// CU20: fill the delivery coordinates from the device GPS, then quote.
  Future<void> _useMyLocation(String branchId) async {
    try {
      if (!await Geolocator.isLocationServiceEnabled()) {
        _warn('Activa la ubicación del dispositivo para usar esta opción.');
        return;
      }
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied) {
        _warn('Necesitamos permiso de ubicación; también puedes escribir la latitud y longitud.');
        return;
      }
      if (permission == LocationPermission.deniedForever) {
        _warn('El permiso de ubicación está bloqueado. Habilítalo en los ajustes del teléfono.');
        await Geolocator.openAppSettings();
        return;
      }
      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, timeLimit: Duration(seconds: 15)),
      );
      if (!mounted) return;
      setState(() {
        _latitude.text = position.latitude.toStringAsFixed(6);
        _longitude.text = position.longitude.toStringAsFixed(6);
      });
      await _quoteDelivery(branchId);
    } catch (_) {
      _warn('No se pudo obtener tu ubicación. Ingrésala manualmente.');
    }
  }

  void _warn(String message) {
    if (mounted) AppSnackBar.show(context, message, tone: AppSnackBarTone.warning);
  }

  Future<void> _quoteDelivery(String branchId) async {
    final latitude = double.tryParse(_latitude.text.trim());
    final longitude = double.tryParse(_longitude.text.trim());
    if (latitude == null || longitude == null) {
      AppSnackBar.show(context, 'Ingresa latitud y longitud válidas.', tone: AppSnackBarTone.warning);
      return;
    }
    setState(() => _quoting = true);
    try {
      final quote = await _controller.api.quoteDelivery(branchId: branchId, latitude: latitude, longitude: longitude);
      if (!mounted) return;
      setState(() => _quote = quote);
      AppSnackBar.show(context, quote['message'].toString(), tone: AppSnackBarTone.success);
    } catch (error) {
      if (!mounted) return;
      setState(() => _quote = null);
      AppSnackBar.show(context, error is ApiException ? error.message : 'No se pudo calcular el envío.',
          tone: AppSnackBarTone.error);
    } finally {
      if (mounted) setState(() => _quoting = false);
    }
  }

  Future<void> _checkoutQr(String pickupBranchId, Map<String, dynamic>? delivery) async {
    try {
      final qr = await _controller.api.checkoutQr(pickupBranchId: pickupBranchId, delivery: delivery, points: _pointsToRedeem);
      if (!mounted) return;
      final client = ApiClient(
        tokenProvider: () => widget.authController.accessToken,
        onUnauthorized: widget.authController.handleUnauthorized,
      );
      await QrPaymentDialog.show(context, client, qr);
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(AppRoutes.orders, arguments: qr['source_id']);
    } catch (error) {
      if (!mounted) return;
      AppSnackBar.show(context, error is ApiException ? error.message : 'No se pudo generar el código QR.',
          tone: AppSnackBarTone.error);
    }
  }

  Future<void> _checkoutStripe({String? pickupBranchId, Map<String, dynamic>? delivery}) async {
    if (AppConfig.stripePublishableKey.isEmpty) {
      AppSnackBar.show(
        context,
        'Configura STRIPE_PUBLISHABLE_KEY para pagar con tarjeta.',
        tone: AppSnackBarTone.error,
      );
      return;
    }

    final result = _isOrderPayment
        ? await _controller.payOrder(orderId: widget.orderId!)
        : await _controller.checkoutStripe(pickupBranchId: pickupBranchId!, delivery: delivery, points: _pointsToRedeem);
    if (!mounted) return;
    if (result == null) {
      AppSnackBar.show(
        context,
        _controller.errorMessage ?? 'No se pudo iniciar el pago.',
        tone: AppSnackBarTone.error,
      );
      return;
    }

    try {
      await Stripe.instance.initPaymentSheet(
        paymentSheetParameters: SetupPaymentSheetParameters(
          merchantDisplayName: 'FashionStore',
          paymentIntentClientSecret: result.checkout.clientSecret,
        ),
      );
      await Stripe.instance.presentPaymentSheet();
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(
        AppRoutes.orders,
        arguments: result.checkout.orderId,
      );
    } on StripeException catch (error) {
      if (!mounted) return;
      AppSnackBar.show(
        context,
        error.error.localizedMessage ?? 'No se pudo completar el pago.',
        tone: AppSnackBarTone.error,
      );
    } catch (_) {
      if (!mounted) return;
      AppSnackBar.show(
        context,
        'No se pudo completar el pago.',
        tone: AppSnackBarTone.error,
      );
    }
  }
}

class _OrderSummary extends StatelessWidget {
  const _OrderSummary({required this.order});

  final Order order;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Pedido ${order.id.substring(0, 8)}',
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          for (final item in order.items)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: SizedBox(
                width: 40,
                height: 48,
                child: ProductImage(imageUrl: item.imageUrl),
              ),
              title: Text(item.productName),
              subtitle: Text('${item.variantSku} · Cantidad ${item.quantity}'),
              trailing: ProductPrice(
                price: item.lineTotal,
                currency: _currencyLabel(order.currency),
              ),
            ),
          const Divider(),
          Align(
            alignment: Alignment.centerRight,
            child: ProductPrice(
              price: order.totalAmount,
              currency: _currencyLabel(order.currency),
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

String _currencyLabel(String currency) {
  return currency.toLowerCase() == 'bob' ? 'Bs' : currency.toUpperCase();
}
