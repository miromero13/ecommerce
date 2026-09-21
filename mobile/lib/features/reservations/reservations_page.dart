import 'package:flutter/material.dart';

import '../../app/theme.dart';
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
import 'reservation_controller.dart';
import 'reservation_models.dart';

class ReservationsPage extends StatefulWidget {
  const ReservationsPage({
    super.key,
    required this.authController,
    this.initialReservationId,
    this.controller,
  });

  final AuthController authController;
  final String? initialReservationId;
  final ReservationController? controller;

  @override
  State<ReservationsPage> createState() => _ReservationsPageState();
}

class _ReservationsPageState extends State<ReservationsPage> {
  late final ReservationController _controller;
  late final bool _ownsController;
  String? _loadedToken;
  bool _initialDetailOpened = false;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller =
        widget.controller ??
        ReservationController(authController: widget.authController);
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
    _loadReservations();
  }

  Future<void> _loadReservations() async {
    await _controller.load();
    if (!mounted || _initialDetailOpened || widget.initialReservationId == null) {
      return;
    }
    _initialDetailOpened = true;
    await _showDetails(widget.initialReservationId!);
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
            title: 'Reservas privadas',
            message: 'Inicia sesión para consultar tus reservas.',
            actionLabel: 'Iniciar sesión',
            onAction: () => LoginDialog.show(
              context: context,
              controller: widget.authController,
            ),
          );
        }
        return ListenableBuilder(
          listenable: _controller,
          builder: (context, _) => _buildReservations(context),
        );
      },
    );
  }

  Widget _buildReservations(BuildContext context) {
    if (_controller.status == ReservationControllerStatus.error &&
        _controller.reservations.isEmpty) {
      return AppErrorView(
        message:
            _controller.errorMessage ?? 'No se pudieron cargar las reservas.',
        onRetry: _loadReservations,
      );
    }
    if (_controller.status == ReservationControllerStatus.loading &&
        _controller.reservations.isEmpty) {
      return const AppLoading(message: 'Cargando reservas...');
    }

    return RefreshIndicator(
      onRefresh: _loadReservations,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          if (_controller.status == ReservationControllerStatus.loading)
            const LinearProgressIndicator(minHeight: 2),
          const AppSectionTitle(
            title: 'Mis reservas',
            subtitle: 'Prepara prendas para probártelas en tienda.',
          ),
          const SizedBox(height: 20),
          if (_controller.reservations.isEmpty)
            AppEmptyView(
              title: 'Aún no tienes reservas',
              message:
                  'Agrega prendas al carrito para reservarlas en una sucursal.',
              actionLabel: 'Ir al carrito',
              onAction: () =>
                  Navigator.of(context).pushReplacementNamed('/cart'),
            )
          else ...[
            for (final reservation in _controller.reservations) ...[
              _ReservationCard(
                reservation: reservation,
                onTap: () => _showDetails(reservation.id),
                onCancel: reservation.canCancel
                    ? () => _cancel(reservation)
                    : null,
                onPurchase: reservation.status == ReservationStatus.attended
                    ? () => _decide(reservation, purchase: true)
                    : null,
                onNotPurchase: reservation.status == ReservationStatus.attended
                    ? () => _decide(reservation, purchase: false)
                    : null,
                onTransfer: reservation.status == ReservationStatus.purchasePending && reservation.cartId == null
                    ? () => _transfer(reservation)
                    : null,
              ),
              const SizedBox(height: 12),
            ],
          ],
        ],
      ),
    );
  }

  Future<void> _cancel(Reservation reservation) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancelar reserva'),
        content: const Text('¿Quieres cancelar esta reserva?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('No'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Cancelar reserva'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await _controller.cancel(reservation.id);
    if (!mounted) return;
    _showFeedback(
      _controller.status == ReservationControllerStatus.error
          ? AppSnackBarTone.error
          : AppSnackBarTone.success,
    );
  }

  Future<void> _showDetails(String reservationId) async {
    await _controller.loadDetail(reservationId);
    if (!mounted || _controller.selectedReservation == null) return;
    final reservation = _controller.selectedReservation!;
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          shrinkWrap: true,
          children: [
            Text(
              'Detalle de reserva',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text(
              '${reservation.branchName} · ${_displayDate(reservation.visitDate)}',
            ),
            const SizedBox(height: 16),
            for (final item in reservation.items)
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
                trailing: ProductPrice(price: item.lineTotal),
              ),
            const Divider(),
            Align(
              alignment: Alignment.centerRight,
              child: ProductPrice(
                price: reservation.totalAmount,
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

  void _showFeedback(AppSnackBarTone tone) {
    final message = tone == AppSnackBarTone.error
        ? _controller.errorMessage
        : _controller.feedbackMessage;
    if (message != null) AppSnackBar.show(context, message, tone: tone);
  }

  Future<void> _decide(Reservation reservation, {required bool purchase}) async {
    await _controller.decide(reservation.id, purchase: purchase);
    if (mounted) _showFeedback(AppSnackBarTone.success);
  }

  Future<void> _transfer(Reservation reservation) async {
    await _controller.transferToCart(reservation.id);
    if (!mounted) return;
    if (_controller.status == ReservationControllerStatus.error) {
      AppSnackBar.show(context, _controller.errorMessage ?? 'No se pudo transferir la reserva.', tone: AppSnackBarTone.error);
      return;
    }
    Navigator.of(context).pushReplacementNamed('/cart');
  }
}

class _ReservationCard extends StatelessWidget {
  const _ReservationCard({
    required this.reservation,
    required this.onTap,
    this.onCancel,
    this.onPurchase,
    this.onNotPurchase,
    this.onTransfer,
  });

  final Reservation reservation;
  final VoidCallback onTap;
  final VoidCallback? onCancel;
  final VoidCallback? onPurchase;
  final VoidCallback? onNotPurchase;
  final VoidCallback? onTransfer;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  reservation.branchName,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Chip(
                label: Text(_statusLabel(reservation.status)),
                backgroundColor: _statusColor(context, reservation.status),
                visualDensity: VisualDensity.compact,
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text('Visita: ${_displayDate(reservation.visitDate)}'),
          Text(
            '${reservation.itemCount} prendas · Bs ${reservation.totalAmount.toStringAsFixed(2)}',
          ),
          if (onCancel != null) ...[
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: onCancel,
                icon: const Icon(Icons.cancel_outlined),
                label: const Text('Cancelar reserva'),
              ),
            ),
          ],
          if (onPurchase != null || onNotPurchase != null) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                if (onPurchase != null)
                  FilledButton(onPressed: onPurchase, child: const Text('Comprar prendas')),
                if (onNotPurchase != null)
                  OutlinedButton(onPressed: onNotPurchase, child: const Text('No comprar')),
              ],
            ),
          ],
          if (onTransfer != null) ...[
            const SizedBox(height: 8),
            Align(alignment: Alignment.centerRight, child: FilledButton(onPressed: onTransfer, child: const Text('Pasar al carrito'))),
          ],
        ],
      ),
    );
  }

  static String _statusLabel(ReservationStatus status) {
    return switch (status) {
      ReservationStatus.pending => 'Pendiente',
      ReservationStatus.confirmed => 'Confirmada',
      ReservationStatus.attended => 'Atendida',
      ReservationStatus.purchasePending => 'Compra pendiente',
      ReservationStatus.sold => 'Vendida',
      ReservationStatus.notSold => 'No comprada',
      ReservationStatus.cancelled => 'Cancelada',
      ReservationStatus.expired => 'Expirada',
    };
  }

  static Color _statusColor(BuildContext context, ReservationStatus status) {
    return switch (status) {
      ReservationStatus.pending => AppColors.coralSoft,
      ReservationStatus.confirmed => const Color(0xFFDDF3E6),
      ReservationStatus.attended => Theme.of(
        context,
        ).colorScheme.surfaceContainerHighest,
      ReservationStatus.purchasePending => const Color(0xFFE9D5FF),
      ReservationStatus.sold => const Color(0xFFDDF3E6),
      ReservationStatus.notSold => Theme.of(context).colorScheme.surfaceContainerHighest,
      ReservationStatus.cancelled ||
      ReservationStatus.expired => Theme.of(context).colorScheme.errorContainer,
    };
  }
}

String _displayDate(DateTime date) {
  final day = date.day.toString().padLeft(2, '0');
  final month = date.month.toString().padLeft(2, '0');
  return '$day/$month/${date.year}';
}
