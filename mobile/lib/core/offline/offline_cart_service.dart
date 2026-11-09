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
        {'variant_id': variantId, 'quantity': quantity, 'created_at': DateTime.now().toIso8601String()},
      ]);
      return savedOfflineMessage;
    }
  }

  /// CU30: envía las prendas guardadas sin conexión. Devuelve los mensajes de las que el servidor rechazó.
  Future<List<String>> syncPending(CartApi api) async {
    final items = await pending();
    final rejected = <String>[];
    while (items.isNotEmpty) {
      final item = items.first;
      try {
        await api.addItem(variantId: item['variant_id'] as String, quantity: item['quantity'] as int);
      } catch (error) {
        if (isOffline(error)) break; // se volvió a cortar: queda pendiente
        rejected.add(error is ApiException ? error.message : 'Una prenda no se pudo agregar al carrito.');
      }
      items.removeAt(0);
      await _save(items);
    }
    return rejected;
  }
}
