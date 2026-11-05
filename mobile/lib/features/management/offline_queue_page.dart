import 'package:flutter/material.dart';
import '../../core/offline/offline_queue_models.dart';
import '../../core/offline/offline_queue_service.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';

class OfflineQueuePage extends StatefulWidget {
  const OfflineQueuePage({super.key, this.queueService});

  final OfflineQueueService? queueService;

  @override
  State<OfflineQueuePage> createState() => _OfflineQueuePageState();
}

class _OfflineQueuePageState extends State<OfflineQueuePage> {
  late final OfflineQueueService _queueService;
  List<OfflineOperation> _operations = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _queueService = widget.queueService ?? OfflineQueueService();
    _loadQueue();
  }

  Future<void> _loadQueue() async {
    setState(() => _loading = true);
    final ops = await _queueService.loadQueue();
    if (mounted) {
      setState(() {
        _operations = ops;
        _loading = false;
      });
    }
  }

  double get _totalAmount =>
      _operations.fold(0.0, (sum, op) => sum + op.total);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cola de Operaciones Offline'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualizar cola',
            onPressed: _loadQueue,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _operations.isEmpty
              ? const AppEmptyView(
                  title: 'Cola local vacía',
                  message: 'No hay transacciones pendientes de sincronizar.',
                )
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    // Resumen métricas
                    AppCard(
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          Column(
                            children: [
                              const Text('Operaciones', style: TextStyle(color: Colors.grey, fontSize: 12)),
                              const SizedBox(height: 4),
                              Text(
                                '${_operations.length}',
                                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                          Container(height: 36, width: 1, color: Colors.grey.shade300),
                          Column(
                            children: [
                              const Text('Total retenido', style: TextStyle(color: Colors.grey, fontSize: 12)),
                              const SizedBox(height: 4),
                              Text(
                                'Bs ${_totalAmount.toStringAsFixed(2)}',
                                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.green),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Operaciones resguardadas localmente:',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    const SizedBox(height: 8),

                    // Lista de operaciones
                    ..._operations.map((op) => _OperationItemCard(operation: op)),
                  ],
                ),
    );
  }
}

class _OperationItemCard extends StatefulWidget {
  const _OperationItemCard({required this.operation});

  final OfflineOperation operation;

  @override
  State<_OperationItemCard> createState() => _OperationItemCardState();
}

class _OperationItemCardState extends State<_OperationItemCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final op = widget.operation;
    final isPending = op.status == 'local_pending';

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(
                    isPending ? Icons.access_time : Icons.sync,
                    color: isPending ? Colors.amber.shade800 : Colors.blue,
                    size: 18,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    op.receiptNumber,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: isPending ? Colors.amber.shade100 : Colors.blue.shade100,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  isPending ? 'Pendiente local' : op.status,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: isPending ? Colors.amber.shade900 : Colors.blue.shade900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            'Fecha: ${op.createdAt.substring(0, op.createdAt.length > 19 ? 19 : op.createdAt.length)}',
            style: const TextStyle(color: Colors.grey, fontSize: 12),
          ),
          const SizedBox(height: 2),
          Text(
            'Cliente: ${op.customerName ?? op.customerEmail ?? "Cliente Mostrador"} • ${op.items.length} prenda(s)',
            style: const TextStyle(color: Colors.grey, fontSize: 12),
          ),
          const Divider(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Total: Bs ${op.total.toStringAsFixed(2)}',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
              TextButton.icon(
                onPressed: () => setState(() => _expanded = !_expanded),
                icon: Icon(_expanded ? Icons.expand_less : Icons.expand_more, size: 16),
                label: Text(_expanded ? 'Ocultar' : 'Auditar prendas', style: const TextStyle(fontSize: 12)),
              ),
            ],
          ),

          // Auditoría de prendas expandida
          if (_expanded) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: op.items.map((it) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(it.productName, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
                              Text(it.variantSku, style: const TextStyle(color: Colors.grey, fontSize: 10)),
                            ],
                          ),
                        ),
                        Text(
                          '${it.quantity} x Bs ${it.unitPrice.toStringAsFixed(2)}',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
