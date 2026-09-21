import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_image.dart';
import '../auth/auth_controller.dart';
import '../auth/login_dialog.dart';
import 'reservation_controller.dart';
import 'reservation_models.dart';

class ReservationCreatePage extends StatefulWidget {
  const ReservationCreatePage({
    super.key,
    required this.authController,
    this.arguments,
    this.controller,
  });

  final AuthController authController;
  final ReservationArguments? arguments;
  final ReservationController? controller;

  @override
  State<ReservationCreatePage> createState() => _ReservationCreatePageState();
}

class _ReservationCreatePageState extends State<ReservationCreatePage> {
  late final ReservationController _controller;
  late final bool _ownsController;
  late final List<ReservationDraftItem> _items;

  String? _loadedToken;
  String? _branchId;
  DateTime _visitDate = _dateOnly(DateTime.now());
  String? _formError;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller = widget.controller ??
        ReservationController(authController: widget.authController);
    _items = [...?widget.arguments?.items];
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
    return Scaffold(
      appBar: AppBar(title: const Text('Preparar reserva')),
      body: ListenableBuilder(
        listenable: widget.authController,
        builder: (context, _) {
          if (widget.authController.status == AuthStatus.loading) {
            return const AppLoading(message: 'Validando sesión...');
          }
          if (widget.authController.status == AuthStatus.error) {
            return AppErrorView(
              message: widget.authController.errorMessage ??
                  'No se pudo validar la sesión.',
              onRetry: widget.authController.restoreSession,
            );
          }
          if (!widget.authController.isAuthenticated) {
            return AppEmptyView(
              title: 'Reservas privadas',
              message: 'Inicia sesión para preparar una reserva.',
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
    if (_items.isEmpty) {
      return AppEmptyView(
        title: 'Reserva sin prendas',
        message: 'Explora el catálogo y agrega al menos una prenda.',
        actionLabel: 'Explorar catálogo',
        onAction: _goToCatalog,
      );
    }
    if (_controller.status == ReservationControllerStatus.error &&
        _controller.branches.isEmpty) {
      return AppErrorView(
        message: _controller.errorMessage ?? 'No se pudo cargar la reserva.',
        onRetry: _controller.load,
      );
    }
    if (_controller.status == ReservationControllerStatus.loading &&
        _controller.branches.isEmpty) {
      return const AppLoading(message: 'Preparando reserva...');
    }

    final branches = _controller.branches.where((branch) => branch.isActive);
    final isSaving = _controller.status == ReservationControllerStatus.saving;
    return AbsorbPointer(
      absorbing: isSaving,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          _summaryCard(context),
          const SizedBox(height: 16),
          AppCard(
            child: DropdownButtonFormField<String>(
              isExpanded: true,
              initialValue: branches.any((branch) => branch.id == _branchId)
                  ? _branchId
                  : null,
              decoration: const InputDecoration(
                labelText: 'Sucursal para visitar',
                prefixIcon: Icon(Icons.store_outlined),
              ),
              hint: const Text('Selecciona una sucursal'),
              items: [
                for (final branch in branches)
                  DropdownMenuItem(
                    value: branch.id,
                    child: Text(
                      '${branch.name} · ${branch.city}',
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
              onChanged: (value) => setState(() => _branchId = value),
            ),
          ),
          const SizedBox(height: 12),
          AppCard(
            onTap: _selectDate,
            child: Row(
              children: [
                const Icon(Icons.calendar_today_outlined),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Fecha de visita',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 4),
                      Text(_humanDate(_visitDate)),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right),
              ],
            ),
          ),
          if (_formError != null) ...[
            const SizedBox(height: 12),
            Text(
              _formError!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ],
          if (_controller.status == ReservationControllerStatus.error &&
              _controller.errorMessage != null) ...[
            const SizedBox(height: 12),
            Text(
              _controller.errorMessage!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ],
          const SizedBox(height: 20),
          AppButton(
            label: 'Confirmar reserva',
            icon: const Icon(Icons.event_available_outlined),
            onPressed: isSaving ? null : _createReservation,
            isLoading: isSaving,
            expand: true,
          ),
        ],
      ),
    );
  }

  Widget _summaryCard(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Prendas seleccionadas',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 12),
          if (_items.isEmpty)
            const Text('No seleccionaste prendas para esta reserva.')
          else
            for (final item in _items) _DraftItemRow(item: item),
          if (_items.isNotEmpty) ...[
            const SizedBox(height: 4),
            AppButton(
              label: 'Agregar otra prenda',
              icon: const Icon(Icons.add_shopping_cart_outlined),
              onPressed: _goToCatalog,
              variant: AppButtonVariant.outlined,
              expand: true,
            ),
          ],
        ],
      ),
    );
  }

  void _goToCatalog() {
    Navigator.of(context).pushReplacementNamed(
      AppRoutes.catalog,
      arguments: ReservationArguments(items: List.of(_items)),
    );
  }

  Future<void> _selectDate() async {
    final selected = await showDatePicker(
      context: context,
      initialDate: _visitDate,
      firstDate: _dateOnly(DateTime.now()),
      lastDate: _dateOnly(DateTime.now()).add(const Duration(days: 365)),
    );
    if (selected != null && mounted) setState(() => _visitDate = selected);
  }

  Future<void> _createReservation() async {
    if (_branchId == null) {
      setState(() => _formError = 'Selecciona una sucursal.');
      return;
    }
    if (_items.isEmpty) {
      setState(() => _formError = 'Agrega al menos una prenda.');
      return;
    }

    setState(() => _formError = null);
    await _controller.create(
      branchId: _branchId!,
      visitDate: _visitDate,
      items: _items,
    );
    if (!mounted) return;
    if (_controller.status == ReservationControllerStatus.ready) {
      final reservationId = _controller.reservations.firstOrNull?.id;
      AppSnackBar.show(
        context,
        _controller.feedbackMessage ?? 'Reserva creada exitosamente.',
        tone: AppSnackBarTone.success,
      );
      Navigator.of(context).pushReplacementNamed(
        AppRoutes.reservations,
        arguments: reservationId,
      );
    } else if (_controller.status == ReservationControllerStatus.error) {
      AppSnackBar.show(
        context,
        _controller.errorMessage ?? 'No se pudo crear la reserva.',
        tone: AppSnackBarTone.error,
      );
    }
  }
}

class _DraftItemRow extends StatelessWidget {
  const _DraftItemRow({required this.item});

  final ReservationDraftItem item;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 64,
            height: 80,
            child: ProductImage(imageUrl: item.imageUrl),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.productName ?? 'Prenda seleccionada',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${item.variantSku ?? item.variantId} · Cantidad ${item.quantity}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

DateTime _dateOnly(DateTime date) => DateTime(date.year, date.month, date.day);

String _humanDate(DateTime date) {
  const weekdays = [
    'lunes',
    'martes',
    'miércoles',
    'jueves',
    'viernes',
    'sábado',
    'domingo',
  ];
  const months = [
    'enero',
    'febrero',
    'marzo',
    'abril',
    'mayo',
    'junio',
    'julio',
    'agosto',
    'septiembre',
    'octubre',
    'noviembre',
    'diciembre',
  ];
  return '${weekdays[date.weekday - 1]} ${date.day} de '
      '${months[date.month - 1]} de ${date.year}';
}
