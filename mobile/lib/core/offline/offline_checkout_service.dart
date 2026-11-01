import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// CU30 (cliente): compra con tarjeta iniciada sin conexión.
/// Stripe no puede cobrar sin internet: se guarda la intención de compra en el dispositivo y,
/// al volver la conexión, se crea el pedido y se abre el pago de Stripe.
/// El pedido solo queda "Pagado" cuando el servidor confirma el cobro con Stripe.
class OfflineCheckoutService {
  OfflineCheckoutService({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _checkoutKey = 'offline_pending_checkout_json';
  static const _branchesKey = 'offline_pickup_branches_json';
  final FlutterSecureStorage _storage;

  Future<Map<String, dynamic>?> pending(String? userId) async {
    final data = await _read(_checkoutKey);
    if (data is! Map || data['user_id'] != userId) return null;
    return Map<String, dynamic>.from(data);
  }

  Future<void> save({
    required String? userId,
    required String pickupBranchId,
    Map<String, dynamic>? delivery,
    int points = 0,
  }) =>
      _storage.write(
        key: _checkoutKey,
        value: jsonEncode({
          'user_id': userId,
          'pickup_branch_id': pickupBranchId,
          'delivery': delivery,
          'points': points,
          'created_at': DateTime.now().toUtc().toIso8601String(),
        }),
      );

  Future<void> clear() => _storage.delete(key: _checkoutKey);

  /// Sucursales de la última carga con conexión, para poder elegir retiro sin internet.
  Future<void> cacheBranches(List<Map<String, dynamic>> branches) =>
      _storage.write(key: _branchesKey, value: jsonEncode(branches));

  Future<List<Map<String, dynamic>>> cachedBranches() async {
    final data = await _read(_branchesKey);
    if (data is! List) return const [];
    return data.whereType<Map>().map(Map<String, dynamic>.from).toList();
  }

  Future<Object?> _read(String key) async {
    try {
      final raw = await _storage.read(key: key);
      return raw == null || raw.isEmpty ? null : jsonDecode(raw);
    } catch (_) {
      return null;
    }
  }
}
