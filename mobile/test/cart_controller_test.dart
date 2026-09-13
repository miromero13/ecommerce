import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/features/cart/cart_api.dart';
import 'package:mobile/features/cart/cart_controller.dart';
import 'package:mobile/features/cart/cart_models.dart';

void main() {
  test('sincroniza el carrito y conserva el mensaje del backend', () async {
    final api = _FakeCartApi();
    final controller = CartController(api: api);

    await controller.load();
    expect(controller.status, CartControllerStatus.ready);
    expect(controller.cart?.itemCount, 0);
    expect(controller.feedbackMessage, 'Carrito obtenido exitosamente');

    await controller.addItem(variantId: 'variant-id', quantity: 1);
    expect(controller.cart?.itemCount, 1);
    expect(controller.feedbackMessage, 'Producto agregado al carrito');

    await controller.updateItem(itemId: 'item-id', quantity: 2);
    expect(controller.cart?.itemCount, 2);

    await controller.removeItem(itemId: 'item-id');
    expect(controller.cart?.itemCount, 0);

    await controller.clear();
    expect(controller.status, CartControllerStatus.ready);
  });

  test('expone ApiException sin reemplazar su mensaje', () async {
    final controller = CartController(
      api: _FakeCartApi(
        failure: const ApiException(statusCode: 400, message: 'Sin stock'),
      ),
    );

    await controller.load();

    expect(controller.status, CartControllerStatus.error);
    expect(controller.errorMessage, 'Sin stock');
  });
}

class _FakeCartApi extends CartApi {
  _FakeCartApi({this.failure}) : super();

  final Object? failure;
  var itemCount = 0;

  @override
  Future<CartOperationResult> getCurrent() async {
    if (failure != null) throw failure!;
    return _result('Carrito obtenido exitosamente');
  }

  @override
  Future<CartOperationResult> addItem({
    required String variantId,
    required int quantity,
  }) async {
    itemCount += quantity;
    return _result('Producto agregado al carrito');
  }

  @override
  Future<CartOperationResult> updateItem({
    required String itemId,
    required int quantity,
  }) async {
    itemCount = quantity;
    return _result('Carrito actualizado exitosamente');
  }

  @override
  Future<CartOperationResult> removeItem({required String itemId}) async {
    itemCount = 0;
    return _result('Producto eliminado del carrito');
  }

  @override
  Future<CartOperationResult> clear() async {
    itemCount = 0;
    return _result('Carrito vaciado exitosamente');
  }

  CartOperationResult _result(String message) {
    return CartOperationResult(cart: _cart(itemCount), message: message);
  }
}

Cart _cart(int itemCount) {
  return Cart(
    id: 'cart-id',
    userId: 'user-id',
    status: CartStatus.active,
    subtotal: itemCount * 100,
    discountAmount: 0,
    totalAmount: itemCount * 100,
    itemCount: itemCount,
    createdAt: DateTime.utc(2026, 1, 1),
    items: const [],
  );
}
