import 'dart:convert';
import 'dart:math';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../network/api_client.dart';
import 'offline_queue_models.dart';

class OfflineQueueService {
  OfflineQueueService({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _queueStorageKey = 'offline_pending_queue_json';
  final FlutterSecureStorage _storage;

  List<OfflineOperation> _operations = [];

  List<OfflineOperation> get operations => List.unmodifiable(_operations);
  int get pendingCount => _operations.where((op) => op.status == 'local_pending' || op.status == 'syncing').length;

  Future<List<OfflineOperation>> loadQueue() async {
    try {
      final jsonStr = await _storage.read(key: _queueStorageKey);
      if (jsonStr != null && jsonStr.isNotEmpty) {
        final decoded = jsonDecode(jsonStr) as List<dynamic>;
        _operations = decoded
            .whereType<Map<String, dynamic>>()
            .map((item) => OfflineOperation.fromJson(item))
            .toList();
      } else {
        _operations = [];
      }
    } catch (_) {
      _operations = [];
    }
    return _operations;
  }

  Future<OfflineOperation> enqueueOperation({
    required String type,
    String? tenantId,
    String? branchId,
    String? customerName,
    String? customerEmail,
    required double subtotal,
    required double discount,
    required double total,
    double? cashReceived,
    double? changeReturned,
    String? notes,
    required List<OfflineOrderItem> items,
  }) async {
    await loadQueue();

    final now = DateTime.now();
    final yyyy = now.year.toString();
    final mm = now.month.toString().padLeft(2, '0');
    final dd = now.day.toString().padLeft(2, '0');
    final randomSuffix = (1000 + Random().nextInt(9000)).toString();
    final receiptNumber = 'CONT-$yyyy$mm$dd-$randomSuffix';

    final operationId = 'mob-${DateTime.now().millisecondsSinceEpoch}-${Random().nextInt(10000)}';

    final operation = OfflineOperation(
      operationId: operationId,
      receiptNumber: receiptNumber,
      type: type,
      status: 'local_pending',
      createdAt: now.toUtc().toIso8601String(),
      tenantId: tenantId,
      branchId: branchId,
      customerName: customerName,
      customerEmail: customerEmail,
      subtotal: subtotal,
      discount: discount,
      total: total,
      cashReceived: cashReceived,
      changeReturned: changeReturned,
      notes: notes,
      items: items,
    );

    _operations.insert(0, operation);
    await _saveQueue();

    return operation;
  }

  Future<void> updateStatus(String operationId, String status, {String? error}) async {
    final index = _operations.indexWhere((op) => op.operationId == operationId);
    if (index != -1) {
      final old = _operations[index];
      _operations[index] = OfflineOperation(
        operationId: old.operationId,
        receiptNumber: old.receiptNumber,
        type: old.type,
        status: status,
        createdAt: old.createdAt,
        tenantId: old.tenantId,
        branchId: old.branchId,
        customerName: old.customerName,
        customerEmail: old.customerEmail,
        subtotal: old.subtotal,
        discount: old.discount,
        total: old.total,
        cashReceived: old.cashReceived,
        changeReturned: old.changeReturned,
        notes: old.notes,
        syncError: error ?? old.syncError,
        items: old.items,
      );
      await _saveQueue();
    }
  }

  Future<void> clearQueue() async {
    _operations.clear();
    await _storage.delete(key: _queueStorageKey);
  }

  /// CU30: Sincroniza las operaciones pendientes con el servidor central
  Future<Map<String, int>> syncQueue(ApiClient apiClient) async {
    await loadQueue();
    final pending = _operations.where((op) => op.status == 'local_pending').toList();
    if (pending.isEmpty) {
      return {'synced': 0, 'conflicts': 0};
    }

    try {
      final payload = {
        'operations': pending.map((op) => op.toJson()).toList(),
      };

      final res = await apiClient.post<Map<String, dynamic>>(
        '/api/offline/queue-sync',
        data: payload,
        parser: (data) => data as Map<String, dynamic>,
      );

      final data = res.data;
      if (data != null) {
        final syncedIds = (data['synced_ids'] as List<dynamic>?)?.cast<String>() ?? [];
        final conflicts = (data['conflicts'] as List<dynamic>?) ?? [];

        _operations.removeWhere((op) => syncedIds.contains(op.operationId));

        for (final conflict in conflicts) {
          if (conflict is Map<String, dynamic>) {
            final opId = conflict['operation_id'] as String?;
            final reason = conflict['reason'] as String?;
            if (opId != null) {
              await updateStatus(opId, 'conflict_rejected', error: reason);
            }
          }
        }

        await _saveQueue();
        return {
          'synced': syncedIds.length,
          'conflicts': conflicts.length,
        };
      }
      return {'synced': 0, 'conflicts': 0};
    } catch (_) {
      return {'synced': 0, 'conflicts': 0};
    }
  }

  Future<void> _saveQueue() async {
    final encoded = jsonEncode(_operations.map((op) => op.toJson()).toList());
    await _storage.write(key: _queueStorageKey, value: encoded);
  }
}
