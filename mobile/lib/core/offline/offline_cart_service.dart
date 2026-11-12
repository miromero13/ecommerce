import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../features/cart/cart_api.dart';
import '../network/api_exception.dart';

/// CU25 (cliente): agregar al carrito sin conexión guarda la prenda en el dispositivo.
/// CU30: al volver la conexión cada prenda se envía al carrito del servidor (POST cart/items).
/// El pago con tarjeta (Stripe) siempre requiere conexión.
class OfflineCartService {
  OfflineCartService({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _storageKey = 'offline_pending_cart_json';
  static const savedOfflineMessage =
      'Sin conexión: guardamos la prenda y se agregará a tu carrito cuando vuelva la conexión.';
  /// The server locks the cart while an order is pending payment (400 with this text).
  static const lockedMessageFragment = 'pedido pendiente de pago';
  static const lockedSyncMessage =
      'Tienes un pedido pendiente de pago: tus prendas guardadas se agregarán cuando lo pagues o lo canceles.';
  /// True after the lock notice was returned: syncing is skipped (no network) until the lock is gone.
  static bool _lockNotified = false;
  static DateTime? _lockedAt;
  /// Overridable clock (tests).
  static DateTime Function() now = DateTime.now;
  static const _lockRetryAfter = Duration(minutes: 5);
  static void resetLockNotice() {
    _lockNotified = false;
    _lockedAt = null;
  }
  final FlutterSecureStorage _storage;

  /// Sin respuesta del servidor (statusCode nulo) = sin conexión.
  static bool isOffline(Object error) => error is ApiException && error.statusCode == null;

  Future<List<Map<String, dynamic>>> pending() async {
    try {
      final raw = await _storage.read(key: _storageKey);
      if (raw == null || raw.isEmpty) return [];
      return (jsonDecode(raw) as List).whereType<Map>().map(Map<String, dynamic>.from).toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> _save(List<Map<String, dynamic>> items) =>
      _storage.write(key: _storageKey, value: jsonEncode(items));

  /// Agrega al carrito del servidor; sin conexión guarda la prenda localmente. Devuelve el mensaje a mostrar.
  Future<String> addItem(CartApi api, {required String variantId, required int quantity}) async {
    try {
      return (await api.addItem(variantId: variantId, quantity: quantity)).message;
    } catch (error) {
      if (!isOffline(error)) rethrow;
      await _save([
        ...await pending(),
        // UTC: the server orders the offline queue by this time.
        {'variant_id': variantId, 'quantity': quantity, 'created_at': DateTime.now().toUtc().toIso8601String()},
      ]);
      return savedOfflineMessage;
    }
  }

  /// CU30: envía las prendas guardadas sin conexión. Devuelve los mensajes de las que el servidor rechazó.
  Future<List<String>> syncPending(CartApi api) async {
    final items = await pending();
    if (items.isEmpty) resetLockNotice();
    // While locked, skip the network; after 5 min try once more (the order may have been paid elsewhere or expired).
    if (_lockNotified && now().difference(_lockedAt!) < _lockRetryAfter) return [];
    final rejected = <String>[];
    while (items.isNotEmpty) {
      final item = items.first;
      try {
        await api.addItem(
          variantId: item['variant_id'] as String,
          quantity: item['quantity'] as int,
          offlineRequestedAt: item['created_at'] as String?,
        );
      } catch (error) {
        if (isOffline(error)) break; // se volvió a cortar: queda pendiente
        if (error is ApiException &&
            error.statusCode == 400 &&
            error.message.contains(lockedMessageFragment)) {
          // Carrito bloqueado: se conservan ésta y las demás prendas; se reintenta en el próximo sync.
          final first = !_lockNotified;
          _lockNotified = true;
          _lockedAt = now();
          return first ? [lockedSyncMessage] : []; // the notice is shown only once
        }
        // Fallo transitorio (sesión vencida, 5xx, límite de peticiones): la prenda se conserva y se reintenta luego.
        if (error is! ApiException || !const [400, 404, 409, 422].contains(error.statusCode)) break;
        rejected.add(error.message);
      }
      items.removeAt(0);
      await _save(items);
    }
    resetLockNotice();
    return rejected;
  }
}
