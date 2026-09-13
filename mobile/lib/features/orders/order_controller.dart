import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../auth/auth_controller.dart';
import 'order_api.dart';
import 'order_models.dart';

enum OrderControllerStatus { idle, loading, saving, ready, error }

class OrderController extends ChangeNotifier {
  OrderController({OrderApi? api, AuthController? authController})
    : _api =
          api ??
          OrderApi(
            client: ApiClient(
              tokenProvider: () => authController?.accessToken,
              onUnauthorized: authController?.handleUnauthorized,
            ),
          );

  final OrderApi _api;

  OrderControllerStatus status = OrderControllerStatus.idle;
  List<Order> orders = const [];
  Order? selectedOrder;
  String? errorMessage;
  String? feedbackMessage;

  Future<void> load() async {
    status = OrderControllerStatus.loading;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();
    try {
      final result = await _api.getMine();
      orders = result.orders;
      feedbackMessage = result.message;
      status = OrderControllerStatus.ready;
    } catch (error) {
      status = OrderControllerStatus.error;
      errorMessage = _messageFor(error);
    }
    notifyListeners();
  }

  Future<void> loadDetail(String orderId) async {
    status = OrderControllerStatus.loading;
    errorMessage = null;
    notifyListeners();
    try {
      final result = await _api.getById(orderId: orderId);
      selectedOrder = result.order;
      feedbackMessage = result.message;
      status = OrderControllerStatus.ready;
    } catch (error) {
      status = OrderControllerStatus.error;
      errorMessage = _messageFor(error);
    }
    notifyListeners();
  }

  Future<void> checkoutCash({String? cashReference}) async {
    status = OrderControllerStatus.saving;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();
    try {
      final result = await _api.checkoutCash(cashReference: cashReference);
      orders = [result.order, ...orders];
      selectedOrder = result.order;
      feedbackMessage = result.message;
      status = OrderControllerStatus.ready;
    } catch (error) {
      status = OrderControllerStatus.error;
      errorMessage = _messageFor(error);
    }
    notifyListeners();
  }

  static String _messageFor(Object error) {
    if (error is ApiException) return error.message;
    return 'No se pudieron sincronizar los pedidos.';
  }
}
