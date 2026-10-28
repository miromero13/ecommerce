import '../../core/network/api_client.dart';

/// CU16: the customer's wishlist (favorites).
class WishlistApi {
  WishlistApi({required ApiClient client}) : _client = client; // ignore: prefer_initializing_formals

  final ApiClient _client;

  Future<List<Map<String, dynamic>>> list() async {
    final response = await _client.get<List<dynamic>>('wishlist', parser: (value) => value as List);
    return (response.data ?? const []).map((row) => Map<String, dynamic>.from(row as Map)).toList();
  }

  Future<String> add(String productId) async =>
      (await _client.post<dynamic>('wishlist/items', data: {'product_id': productId})).message;

  Future<String> remove(String productId) async =>
      (await _client.delete<dynamic>('wishlist/items/$productId')).message;

  Future<String> moveToCart(String productId, String variantId) async => (await _client.post<dynamic>(
        'wishlist/items/$productId/move-to-cart',
        data: {'variant_id': variantId},
      ))
          .message;
}
