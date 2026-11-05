import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/network/api_exception.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_snack_bar.dart';
import 'rma_api.dart';
import 'rma_models.dart';

class _ItemDraft {
  _ItemDraft({
    required this.item,
    this.requestedVariantId,
  });

  final EligibleOrderItem item;
  bool selected = false;
  String reason = 'size_change';
  String preferredResolution = 'exchange';
  String? requestedVariantId;
  String notes = '';
}

class RmaCreateDialog extends StatefulWidget {
  const RmaCreateDialog({
    super.key,
    required this.api,
  });

  final RmaApi api;

  static Future<bool?> show(BuildContext context, {required RmaApi api}) {
    return showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => RmaCreateDialog(api: api),
    );
  }

  @override
  State<RmaCreateDialog> createState() => _RmaCreateDialogState();
}

class _RmaCreateDialogState extends State<RmaCreateDialog> {
  bool _loading = true;
  bool _submitting = false;
  String? _error;
  List<EligibleOrder> _orders = const [];
  EligibleOrder? _selectedOrder;
  final Map<String, _ItemDraft> _drafts = {};
  final TextEditingController _generalNotesController = TextEditingController();

  @override
  void initState() {
    super.initState();
    unawaited(_load());
  }

  @override
  void dispose() {
    _generalNotesController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final list = await widget.api.getEligibleOrders();
      if (!mounted) return;
      setState(() {
        _orders = list;
        _loading = false;
        if (_orders.isNotEmpty) {
          _selectOrder(_orders.first);
        }
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
        _error = 'No se pudieron consultar tus compras elegibles.';
        _loading = false;
      });
    }
  }

  void _selectOrder(EligibleOrder order) {
    setState(() {
      _selectedOrder = order;
      _drafts.clear();
      for (final it in order.items) {
        if (it.eligibleForRma) {
          String? defaultVar;
          if (it.sameProductVariants.isNotEmpty) {
            final available = it.sameProductVariants.where((v) => v.stock > 0).toList();
            defaultVar = (available.isNotEmpty ? available.first : it.sameProductVariants.first).variantId;
          }
          _drafts[it.orderItemId] = _ItemDraft(
            item: it,
            requestedVariantId: defaultVar,
          );
        }
      }
    });
  }

  Future<void> _submit() async {
    if (_selectedOrder == null) return;

    final selectedDrafts = _drafts.values.where((d) => d.selected).toList();
    if (selectedDrafts.isEmpty) {
      AppSnackBar.show(
        context,
        'Selecciona al menos una prenda para cambiar o devolver.',
        tone: AppSnackBarTone.error,
      );
      return;
    }

    setState(() => _submitting = true);

    try {
      final payloadItems = selectedDrafts.map((d) {
        return {
          'order_item_id': d.item.orderItemId,
          'quantity': 1,
          'reason': d.reason,
          'preferred_resolution': d.preferredResolution,
          if (d.preferredResolution == 'exchange' && d.requestedVariantId != null)
            'requested_variant_id': d.requestedVariantId,
          if (d.notes.trim().isNotEmpty) 'customer_notes': d.notes.trim(),
        };
      }).toList(growable: false);

      final res = await widget.api.createRmaRequest(
        orderId: _selectedOrder!.orderId,
        items: payloadItems,
        customerNotes: _generalNotesController.text.trim().isNotEmpty
            ? _generalNotesController.text.trim()
            : null,
      );

      if (!mounted) return;
      AppSnackBar.show(
        context,
        res.message.isNotEmpty
            ? res.message
            : 'Solicitud de cambio/devolución registrada con éxito.',
        tone: AppSnackBarTone.success,
      );
      Navigator.of(context).pop(true);
    } on ApiException catch (e) {
      if (!mounted) return;
      AppSnackBar.show(context, e.message, tone: AppSnackBarTone.error);
    } catch (_) {
      if (!mounted) return;
      AppSnackBar.show(
        context,
        'Ocurrió un error al registrar la solicitud.',
        tone: AppSnackBarTone.error,
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return DraggableScrollableSheet(
      initialChildSize: 0.88,
      maxChildSize: 0.95,
      minChildSize: 0.5,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: theme.scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              Container(
                margin: const EdgeInsets.only(top: 10, bottom: 8),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade400,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Row(
                  children: [
                    const Icon(Icons.assignment_return_outlined, color: Colors.blue),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Solicitar Devolución o Cambio',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              Expanded(
                child: _buildContent(scrollController),
              ),
              if (!_loading && _orders.isNotEmpty)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: theme.cardColor,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.05),
                        blurRadius: 10,
                        offset: const Offset(0, -4),
                      ),
                    ],
                  ),
                  child: AppButton(
                    label: _submitting ? 'Enviando solicitud...' : 'Confirmar solicitud',
                    icon: const Icon(Icons.check),
                    isLoading: _submitting,
                    onPressed: _submitting ? null : _submit,
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildContent(ScrollController scrollController) {
    if (_loading) {
      return const AppLoading(message: 'Cargando compras elegibles...');
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              AppButton(label: 'Reintentar', onPressed: _load),
            ],
          ),
        ),
      );
    }

    if (_orders.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.info_outline, size: 48, color: Colors.grey),
              const SizedBox(height: 12),
              const Text(
                'No tienes compras elegibles',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 6),
              const Text(
                'Solo se pueden solicitar cambios y devoluciones para compras entregadas dentro de los últimos 30 días.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey),
              ),
            ],
          ),
        ),
      );
    }

    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          '1. Selecciona el pedido que contiene la prenda:',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<EligibleOrder>(
          isExpanded: true,
          value: _selectedOrder,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          ),
          items: _orders.map((ord) {
            return DropdownMenuItem(
              value: ord,
              child: Text(
                'Pedido #${ord.orderNumber} (${ord.items.length} prendas) · Hace ${ord.daysSinceDelivery} d',
                overflow: TextOverflow.ellipsis,
              ),
            );
          }).toList(),
          onChanged: (val) {
            if (val != null) _selectOrder(val);
          },
        ),
        const SizedBox(height: 20),
        const Text(
          '2. Selecciona las prendas a devolver o cambiar:',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        const SizedBox(height: 8),
        for (final item in _selectedOrder?.items ?? <EligibleOrderItem>[])
          _buildItemCard(item),
        const SizedBox(height: 16),
        const Text(
          '3. Comentario general (opcional):',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _generalNotesController,
          maxLines: 2,
          decoration: const InputDecoration(
            hintText: 'Aclaraciones adicionales sobre tu entrega en sucursal...',
            border: OutlineInputBorder(),
          ),
        ),
      ],
    );
  }

  Widget _buildItemCard(EligibleOrderItem item) {
    final draft = _drafts[item.orderItemId];
    if (draft == null) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(
                item.productName,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              subtitle: Text(
                'Talle: ${item.sizeName ?? 'Único'} · Color: ${item.colorName ?? 'Estándar'} · SKU: ${item.sku}',
              ),
              value: draft.selected,
              onChanged: (val) {
                setState(() => draft.selected = val ?? false);
              },
            ),
            if (draft.selected) ...[
              const Divider(height: 16),
              const Text(
                'Motivo del reclamo:',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              DropdownButtonFormField<String>(
                value: draft.reason,
                isExpanded: true,
                decoration: const InputDecoration(
                  contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'size_change', child: Text('Cambio de talle')),
                  DropdownMenuItem(value: 'color_change', child: Text('Cambio de color')),
                  DropdownMenuItem(value: 'factory_defect', child: Text('Defecto / Falla de fábrica')),
                  DropdownMenuItem(value: 'not_as_expected', child: Text('No es lo que esperaba')),
                ],
                onChanged: (val) {
                  if (val != null) setState(() => draft.reason = val);
                },
              ),
              const SizedBox(height: 10),
              const Text(
                'Resolución deseada:',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              DropdownButtonFormField<String>(
                value: draft.preferredResolution,
                isExpanded: true,
                decoration: const InputDecoration(
                  contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(
                    value: 'exchange',
                    child: Text('Cambio por otra prenda / talle'),
                  ),
                  DropdownMenuItem(
                    value: 'store_credit',
                    child: Text('Saldo en Billetera Digital (Crédito)'),
                  ),
                ],
                onChanged: (val) {
                  if (val != null) setState(() => draft.preferredResolution = val);
                },
              ),
              if (draft.preferredResolution == 'exchange' && item.sameProductVariants.isNotEmpty) ...[
                const SizedBox(height: 10),
                const Text(
                  'Variante de cambio deseada:',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                DropdownButtonFormField<String>(
                  value: draft.requestedVariantId,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                    border: OutlineInputBorder(),
                  ),
                  items: item.sameProductVariants.map((v) {
                    return DropdownMenuItem(
                      value: v.variantId,
                      child: Text(v.label, overflow: TextOverflow.ellipsis),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) setState(() => draft.requestedVariantId = val);
                  },
                ),
              ],
              const SizedBox(height: 10),
              TextField(
                onChanged: (val) => draft.notes = val,
                decoration: const InputDecoration(
                  labelText: 'Observación específica de la prenda',
                  hintText: 'Ej. Necesito un talle más grande o tiene una costura descosida',
                  contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
