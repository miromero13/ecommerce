import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/network/api_exception.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_dialog.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../auth/auth_controller.dart';
import 'rma_api.dart';
import 'rma_create_dialog.dart';
import 'rma_models.dart';

class RmaPage extends StatefulWidget {
  const RmaPage({
    super.key,
    required this.authController,
  });

  final AuthController authController;

  @override
  State<RmaPage> createState() => _RmaPageState();
}

class _RmaPageState extends State<RmaPage> {
  late final RmaApi _api;
  bool _loading = false;
  String? _error;
  List<RmaRequest> _requests = const [];

  @override
  void initState() {
    super.initState();
    _api = RmaApi(
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
      final list = await _api.getMyRmaRequests();
      if (!mounted) return;
      setState(() {
        _requests = list;
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
        _error = 'No se pudieron consultar tus solicitudes de devolución.';
        _loading = false;
      });
    }
  }

  Future<void> _openCreate() async {
    final created = await RmaCreateDialog.show(context, api: _api);
    if (created == true) {
      unawaited(_load());
    }
  }

  void _showSlipDialog(RmaRequest request) {
    AppDialog.show<void>(
      context: context,
      title: 'Ficha de Solicitud #${request.rmaNumber}',
      content: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue.shade200),
              ),
              child: Row(
                children: [
                  Icon(Icons.description_outlined, color: Colors.blue.shade700),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Ficha Oficial de Cambio / Devolución',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.blue.shade900,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Text('Orden asociada: #${request.orderNumber}'),
            Text('Estado actual: ${request.statusLabel}'),
            Text('Fecha de emisión: ${_formatDate(request.createdAt)}'),
            const SizedBox(height: 10),
            const Text(
              'Prendas incluidas:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            for (final it in request.items)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text('• ${it.productName} (${it.reasonLabel} ➔ ${it.resolutionLabel})'),
              ),
            const SizedBox(height: 12),
            const Text(
              'Presenta este número en caja o sucursal para la inspección física de las prendas.',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Entendido'),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis Devoluciones y Cambios'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualizar',
            onPressed: _loading ? null : () => unawaited(_load()),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openCreate,
        icon: const Icon(Icons.add),
        label: const Text('Nueva solicitud'),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading && _requests.isEmpty) {
      return const AppLoading(message: 'Cargando solicitudes de cambio y devolución...');
    }

    if (_error != null && _requests.isEmpty) {
      return AppErrorView(
        message: _error!,
        onRetry: () => unawaited(_load()),
      );
    }

    if (_requests.isEmpty) {
      return AppEmptyView(
        title: 'No tienes solicitudes de cambio',
        message:
            'Gestiona cambios de talle o devoluciones de tus compras dentro de los 30 días posteriores a la entrega.',
        actionLabel: 'Crear solicitud',
        onAction: _openCreate,
      );
    }

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
        itemCount: _requests.length,
        separatorBuilder: (context, _) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final request = _requests[index];
          return _RmaCard(
            request: request,
            onViewSlip: () => _showSlipDialog(request),
          );
        },
      ),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
  }
}

class _RmaCard extends StatelessWidget {
  const _RmaCard({
    required this.request,
    required this.onViewSlip,
  });

  final RmaRequest request;
  final VoidCallback onViewSlip;

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
                child: Row(
                  children: [
                    const Icon(Icons.assignment_return_outlined, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      request.rmaNumber,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              _buildBadge(context),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Pedido #${request.orderNumber} · Solicitado el ${_formatDate(request.createdAt)}',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 12),
          const Divider(height: 1),
          const SizedBox(height: 10),
          for (final item in request.items) ...[
            _buildItemRow(context, item),
            const SizedBox(height: 8),
          ],
          if (request.customerNotes != null && request.customerNotes!.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              'Nota: ${request.customerNotes}',
              style: theme.textTheme.bodySmall?.copyWith(
                fontStyle: FontStyle.italic,
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              OutlinedButton.icon(
                icon: const Icon(Icons.description_outlined, size: 16),
                label: const Text('Ver Ficha'),
                onPressed: onViewSlip,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildItemRow(BuildContext context, RmaItem item) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  item.productName,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.blue.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  item.statusLabel,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: Colors.blue.shade800,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Text(
            'Motivo: ${item.reasonLabel} ➔ Resolución: ${item.resolutionLabel}',
            style: theme.textTheme.bodySmall,
          ),
          if (item.requestedVariantLabel != null)
            Text(
              'Prenda solicitada para cambio: ${item.requestedVariantLabel}',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.primary,
                fontWeight: FontWeight.w600,
              ),
            ),
          if (item.quarantineRecord != null) ...[
            const SizedBox(height: 2),
            Text(
              'Acta técnica de merma: ${item.quarantineRecord}',
              style: const TextStyle(fontSize: 11, color: Colors.purple, fontWeight: FontWeight.bold),
            ),
          ],
          if (item.refundAmount != null && item.refundAmount! > 0) ...[
            const SizedBox(height: 2),
            Text(
              'Monto devuelto a Billetera: ${item.refundAmount!.toStringAsFixed(2)} Bs',
              style: const TextStyle(fontSize: 11, color: Colors.green, fontWeight: FontWeight.bold),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBadge(BuildContext context) {
    final color = switch (request.status) {
      'approved' || 'completed' => Colors.green,
      'rejected' => Colors.red,
      'partially_approved' => Colors.teal,
      _ => Colors.orange,
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        border: Border.all(color: color.withValues(alpha: 0.4)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        request.statusLabel,
        style: TextStyle(
          color: color.shade800,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
  }
}
