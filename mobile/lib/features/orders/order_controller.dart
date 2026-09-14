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
  List<PickupBranch> pickupBranches = const [];
  Order? selectedOrder;
  String? errorMessage;
  String? feedbackMessage;

  Future<void> load() async {
    status = OrderControllerStatus.loading;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();
    try {
      final results = await Future.wait([
        _api.getMine(),
        _api.getPublicBranches(),
      ]);
      final result = results.first as OrderListResult;
      orders = result.orders;
      pickupBranches = results.last as List<PickupBranch>;
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

  Future<void> checkoutCash({required String pickupBranchId}) async {
    status = OrderControllerStatus.saving;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();
    try {
      final result = await _api.checkoutCash(pickupBranchId: pickupBranchId);
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

  Future<StripeCheckoutResult?> checkoutStripe({
    required String pickupBranchId,
  }) async {
    status = OrderControllerStatus.saving;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();
    try {
      final result = await _api.checkoutStripe(pickupBranchId: pickupBranchId);
      feedbackMessage = result.message;
      status = OrderControllerStatus.ready;
      notifyListeners();
      return result;
    } catch (error) {
      status = OrderControllerStatus.error;
      errorMessage = _messageFor(error);
      notifyListeners();
      return null;
    }
  }

  static String _messageFor(Object error) {
    if (error is ApiException) return error.message;
    return 'No se pudieron sincronizar los pedidos.';
  }
}
