import '../../core/network/api_client.dart';
import 'cart_models.dart';

class CartApi {
  CartApi({
    ApiClient? client,
    TokenProvider? tokenProvider,
    UnauthorizedHandler? onUnauthorized,
  }) : _client =
           client ??
           ApiClient(
             tokenProvider: tokenProvider,
             onUnauthorized: onUnauthorized,
           );

  final ApiClient _client;

  Future<CartOperationResult> getCurrent() async {
    final response = await _client.get<Cart>(
      'cart/current',
      parser: _parseCart,
    );
    return _result(response.data, response.message);
  }

  Future<CartOperationResult> addItem({
    required String variantId,
    required int quantity,
  }) async {
    final response = await _client.post<Cart>(
      'cart/items',
      data: {'variant_id': variantId, 'quantity': quantity},
      parser: _parseCart,
    );
    return _result(response.data, response.message);
  }

  Future<CartOperationResult> updateItem({
    required String itemId,
    required int quantity,
  }) async {
    final response = await _client.patch<Cart>(
      'cart/items/$itemId',
      data: {'quantity': quantity},
      parser: _parseCart,
    );
    return _result(response.data, response.message);
  }

  Future<CartOperationResult> removeItem({required String itemId}) async {
    final response = await _client.delete<Cart>(
      'cart/items/$itemId',
      parser: _parseCart,
    );
    return _result(response.data, response.message);
  }

  Future<CartOperationResult> clear() async {
    final response = await _client.delete<Cart>(
      'cart/current',
      parser: _parseCart,
    );
    return _result(response.data, response.message);
  }

  static Cart _parseCart(dynamic value) {
    if (value is! Map) {
      throw const FormatException('La respuesta del carrito es inválida');
    }
    return Cart.fromJson(Map<String, dynamic>.from(value));
  }

  static CartOperationResult _result(Cart? cart, String message) {
    if (cart == null) {
      throw const FormatException('La respuesta del carrito no contiene datos');
    }
    return CartOperationResult(cart: cart, message: message);
  }
}
