import 'package:flutter/material.dart';

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

class OrdersPage extends StatefulWidget {
  const OrdersPage({super.key, required this.authController, this.controller});

  final AuthController authController;
  final OrderController? controller;

  @override
  State<OrdersPage> createState() => _OrdersPageState();
}

class _OrdersPageState extends State<OrdersPage> {
  late final OrderController _controller;
  late final bool _ownsController;
  String? _loadedToken;

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
    _controller.load();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
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
            title: 'Pedidos privados',
            message: 'Inicia sesión para consultar tus pedidos.',
            actionLabel: 'Iniciar sesión',
            onAction: () => LoginDialog.show(
              context: context,
              controller: widget.authController,
            ),
          );
        }
        return ListenableBuilder(
          listenable: _controller,
          builder: (context, _) => _buildOrders(context),
        );
      },
    );
  }

  Widget _buildOrders(BuildContext context) {
    if (_controller.status == OrderControllerStatus.error &&
        _controller.orders.isEmpty) {
      return AppErrorView(
        message:
            _controller.errorMessage ?? 'No se pudieron cargar los pedidos.',
        onRetry: _controller.load,
      );
    }
    if (_controller.status == OrderControllerStatus.loading &&
        _controller.orders.isEmpty) {
      return const AppLoading(message: 'Cargando pedidos...');
    }

    return RefreshIndicator(
      onRefresh: _controller.load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          if (_controller.status == OrderControllerStatus.loading)
            const LinearProgressIndicator(minHeight: 2),
          const AppSectionTitle(
            title: 'Mis pedidos',
            subtitle: 'Consulta el estado y el detalle de tus compras.',
          ),
          const SizedBox(height: 16),
          _checkoutCard(context),
          const SizedBox(height: 20),
          if (_controller.orders.isEmpty)
            const AppEmptyView(
              title: 'Aún no tienes pedidos',
              message: 'Tus compras confirmadas aparecerán aquí.',
            )
          else
            for (final order in _controller.orders) ...[
              _OrderCard(order: order, onTap: () => _showDetails(order.id)),
              const SizedBox(height: 12),
            ],
        ],
      ),
    );
  }

  Widget _checkoutCard(BuildContext context) {
    final isSaving = _controller.status == OrderControllerStatus.saving;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Finalizar compra',
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          const Text('El pedido se registrará con pago en efectivo.'),
          const SizedBox(height: 12),
          AppButton(
            label: 'Comprar con efectivo',
            icon: const Icon(Icons.payments_outlined),
            onPressed: isSaving ? null : _checkout,
            isLoading: isSaving,
            expand: true,
          ),
        ],
      ),
    );
  }

  Future<void> _checkout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmar compra'),
        content: const Text(
          'Se creará un pedido con los productos del carrito y pago en efectivo.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Volver'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await _controller.checkoutCash();
    if (!mounted) return;
    final isError = _controller.status == OrderControllerStatus.error;
    final message = isError
        ? _controller.errorMessage
        : _controller.feedbackMessage;
    if (message != null) {
      AppSnackBar.show(
        context,
        message,
        tone: isError ? AppSnackBarTone.error : AppSnackBarTone.success,
      );
    }
  }

  Future<void> _showDetails(String orderId) async {
    await _controller.loadDetail(orderId);
    if (!mounted || _controller.selectedOrder == null) return;
    final order = _controller.selectedOrder!;
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          shrinkWrap: true,
          children: [
            Text(
              'Detalle de pedido',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text('Estado: ${_statusLabel(order.status)}'),
            Text('Pago: ${_paymentStatusLabel(order.paymentStatus)}'),
            const SizedBox(height: 16),
            for (final item in order.items)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: SizedBox(
                  width: 48,
                  height: 56,
                  child: ProductImage(imageUrl: item.imageUrl),
                ),
                title: Text(item.productName),
                subtitle: Text(
                  '${item.variantSku} · Cantidad ${item.quantity}',
                ),
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
      ),
    );
  }
}

class _OrderCard extends StatelessWidget {
  const _OrderCard({required this.order, required this.onTap});

  final Order order;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      onTap: onTap,
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: Theme.of(context).colorScheme.primaryContainer,
            child: Icon(
              Icons.receipt_long_outlined,
              color: Theme.of(context).colorScheme.onPrimaryContainer,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Pedido ${order.id.substring(0, 8)}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${_statusLabel(order.status)} · ${order.items.length} ítems',
                ),
                Text(_displayDate(order.createdAt)),
              ],
            ),
          ),
          ProductPrice(
            price: order.totalAmount,
            currency: _currencyLabel(order.currency),
          ),
        ],
      ),
    );
  }
}

String _statusLabel(OrderStatus status) {
  return switch (status) {
    OrderStatus.pending => 'Pendiente',
    OrderStatus.paid => 'Pagado',
    OrderStatus.failed => 'Fallido',
    OrderStatus.cancelled => 'Cancelado',
  };
}

String _paymentStatusLabel(PaymentStatus status) {
  return switch (status) {
    PaymentStatus.pending => 'Pendiente',
    PaymentStatus.paid => 'Pagado',
    PaymentStatus.failed => 'Fallido',
  };
}

String _currencyLabel(String currency) {
  return currency.toLowerCase() == 'bob' ? 'Bs' : currency.toUpperCase();
}

String _displayDate(DateTime date) {
  final local = date.toLocal();
  return '${local.day.toString().padLeft(2, '0')}/'
      '${local.month.toString().padLeft(2, '0')}/${local.year}';
}
