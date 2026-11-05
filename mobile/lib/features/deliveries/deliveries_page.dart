import 'dart:async';

import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../core/network/api_exception.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../auth/auth_controller.dart';
import 'delivery_api.dart';
import 'delivery_models.dart';

class DeliveriesPage extends StatefulWidget {
  const DeliveriesPage({
    super.key,
    required this.authController,
  });

  final AuthController authController;

  @override
  State<DeliveriesPage> createState() => _DeliveriesPageState();
}

class _DeliveriesPageState extends State<DeliveriesPage> {
  late final DeliveryApi _api;
  bool _loading = false;
  String? _error;
  List<DeliveryOrder> _deliveries = const [];

  @override
  void initState() {
    super.initState();
    _api = DeliveryApi(
      tokenProvider: () => widget.authController.accessToken,
      onUnauthorized: widget.authController.handleUnauthorized,
    );
    unawaited(_load());
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final list = await _api.getMyDeliveries();
      if (!mounted) return;
      setState(() {
        _deliveries = list;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'No se pudieron cargar tus envíos a domicilio.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis Envíos a Domicilio'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualizar',
            onPressed: _loading ? null : () => unawaited(_load()),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading && _deliveries.isEmpty) {
      return const AppLoading(message: 'Consultando estado de tus envíos...');
    }

    if (_error != null && _deliveries.isEmpty) {
      return AppErrorView(
        message: _error!,
        onRetry: () => unawaited(_load()),
      );
    }

    if (_deliveries.isEmpty) {
      return AppEmptyView(
        title: 'No tienes envíos registrados',
        message:
            'Tus compras con despacho a domicilio y código PIN aparecerán acá.',
        actionLabel: 'Ver catálogo',
        onAction: () => Navigator.of(context).pushNamed(AppRoutes.catalog),
      );
    }

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        itemCount: _deliveries.length,
        separatorBuilder: (context, _) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final delivery = _deliveries[index];
          return _DeliveryCard(delivery: delivery);
        },
      ),
    );
  }
}

class _DeliveryCard extends StatelessWidget {
  const _DeliveryCard({required this.delivery});

  final DeliveryOrder delivery;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  'Orden #${delivery.orderId.length > 8 ? delivery.orderId.substring(0, 8) : delivery.orderId}',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              _buildBadge(context),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Origen: ${delivery.tenantName}${delivery.branchName != null ? ' (${delivery.branchName})' : ''}',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.amber.shade50,
              border: Border.all(color: Colors.amber.shade300),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.vpn_key_outlined,
                  color: Colors.amber.shade900,
                  size: 28,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'CÓDIGO PIN DE SEGURIDAD',
                        style: theme.textTheme.labelSmall?.copyWith(
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                          color: Colors.amber.shade900,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        delivery.deliveryPin ?? '----',
                        style: const TextStyle(
                          fontFamily: 'monospace',
                          fontWeight: FontWeight.w900,
                          fontSize: 22,
                          letterSpacing: 4,
                          color: Colors.black87,
                        ),
                      ),
                    ],
                  ),
                ),
                Text(
                  delivery.status == 'delivered' ? 'Entregado' : 'PIN para chofer',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: Colors.amber.shade900,
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.location_on_outlined, size: 16),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Dirección: ${delivery.address}${delivery.reference != null ? ' (${delivery.reference})' : ''}',
                  style: theme.textTheme.bodySmall,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              const Icon(Icons.person_outline, size: 16),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Repartidor: ${delivery.driverName ?? 'Pendiente de asignación'}',
                  style: theme.textTheme.bodySmall,
                ),
              ),
              Text(
                '${delivery.totalAmount.toStringAsFixed(2)} ${delivery.currency.toUpperCase()}',
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: theme.colorScheme.primary,
                ),
              ),
            ],
          ),
          if (delivery.deliveredAt != null) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.check_circle_outline, size: 14, color: Colors.green.shade700),
                const SizedBox(width: 4),
                Text(
                  'Entregado el ${_formatDate(delivery.deliveredAt!)}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: Colors.green.shade700,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBadge(BuildContext context) {
    final color = switch (delivery.status) {
      'in_transit' => Colors.blue,
      'delivered' => Colors.green,
      'ready_for_pickup' || 'pending_pickup' => Colors.orange,
      _ => Colors.grey,
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        border: Border.all(color: color.withValues(alpha: 0.4)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        delivery.statusLabel,
        style: TextStyle(
          color: color.shade800,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }
}
