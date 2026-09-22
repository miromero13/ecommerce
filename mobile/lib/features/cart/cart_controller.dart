import 'package:flutter/foundation.dart';

import '../../core/network/api_exception.dart';
import 'cart_api.dart';
import 'cart_models.dart';

enum CartControllerStatus { idle, loading, ready, error }

class CartController extends ChangeNotifier {
  CartController({CartApi? api}) : _api = api ?? CartApi();

  final CartApi _api;

  CartControllerStatus status = CartControllerStatus.idle;
  Cart? cart;
  String? errorMessage;
  String? feedbackMessage;

  Future<void> load() => _run(_api.getCurrent);

  Future<void> addItem({required String variantId, required int quantity}) {
    return _run(() => _api.addItem(variantId: variantId, quantity: quantity));
  }

  Future<void> updateItem({required String itemId, required int quantity}) {
    return _run(() => _api.updateItem(itemId: itemId, quantity: quantity));
  }

  Future<void> removeItem({required String itemId}) {
    return _run(() => _api.removeItem(itemId: itemId));
  }

  Future<void> clear() => _run(_api.clear);

  Future<void> applyCoupon(String code) =>
      _run(() => _api.applyCoupon(code: code));

  Future<void> removeCoupon() => _run(_api.removeCoupon);

  Future<void> _run(Future<CartOperationResult> Function() operation) async {
    status = CartControllerStatus.loading;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();

    try {
      final result = await operation();
      cart = result.cart;
      feedbackMessage = result.message;
      status = CartControllerStatus.ready;
    } catch (error) {
      status = CartControllerStatus.error;
      errorMessage = error is ApiException
          ? error.message
          : 'No se pudo sincronizar el carrito.';
    }
    notifyListeners();
  }
}
