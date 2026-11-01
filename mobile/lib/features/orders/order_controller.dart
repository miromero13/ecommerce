import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/offline/offline_cart_service.dart';
import '../../core/offline/offline_checkout_service.dart';
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
  OrderApi get api => _api;
  final _offlineCheckout = OfflineCheckoutService();

  /// True when the last request got no answer from the server (no connection).
  bool isOffline = false;

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
      isOffline = false;
      status = OrderControllerStatus.ready;
      await _offlineCheckout.cacheBranches(pickupBranches.map((b) => b.toJson()).toList());
    } catch (error) {
      errorMessage = _messageFor(error);
      isOffline = OfflineCartService.isOffline(error);
      // CU30: sin conexión se usan las sucursales guardadas para poder dejar la compra pendiente.
      final cached = isOffline ? await _offlineCheckout.cachedBranches() : const <Map<String, dynamic>>[];
      if (cached.isNotEmpty) {
        pickupBranches = cached.map(PickupBranch.fromJson).toList(growable: false);
        status = OrderControllerStatus.ready;
      } else {
        status = OrderControllerStatus.error;
      }
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

  Future<StripeCheckoutResult?> checkoutStripe({
    required String pickupBranchId,
    Map<String, dynamic>? delivery,
    int points = 0,
    String? offlineRequestedAt,
  }) async {
    status = OrderControllerStatus.saving;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();
    try {
      final result = await _api.checkoutStripe(
        pickupBranchId: pickupBranchId,
        delivery: delivery,
        points: points,
        offlineRequestedAt: offlineRequestedAt,
      );
      feedbackMessage = result.message;
      status = OrderControllerStatus.ready;
      notifyListeners();
      return result;
    } catch (error) {
      status = OrderControllerStatus.error;
      errorMessage = _messageFor(error);
      isOffline = OfflineCartService.isOffline(error);
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> checkoutWallet({
    required String pickupBranchId,
    Map<String, dynamic>? delivery,
    int points = 0,
  }) async {
    status = OrderControllerStatus.saving;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();
    try {
      final result = await _api.checkoutWallet(pickupBranchId: pickupBranchId, delivery: delivery, points: points);
      feedbackMessage = 'Pedido pagado exitosamente con tu Billetera Digital';
      status = OrderControllerStatus.ready;
      notifyListeners();
      return result;
    } catch (error) {
      status = OrderControllerStatus.error;
      errorMessage = _messageFor(error);
      isOffline = OfflineCartService.isOffline(error);
      notifyListeners();
      return null;
    }
  }

  Future<StripeCheckoutResult?> payOrder({required String orderId}) async {
    status = OrderControllerStatus.saving;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();
    try {
      final result = await _api.payOrder(orderId: orderId);
      feedbackMessage = result.message;
      status = OrderControllerStatus.ready;
      notifyListeners();
      return result;
    } catch (error) {
      status = OrderControllerStatus.error;
      errorMessage = _messageFor(error);
      isOffline = OfflineCartService.isOffline(error);
      notifyListeners();
      return null;
    }
  }

  /// Returns true when the order was cancelled (the cart is unlocked on the server).
  Future<bool> cancelOrder({required String orderId}) async {
    errorMessage = null;
    try {
      feedbackMessage = await _api.cancelOrder(orderId: orderId);
      return true;
    } catch (error) {
      errorMessage = _messageFor(error);
      return false;
    }
  }

  static String _messageFor(Object error) {
    if (error is ApiException) return error.message;
    return 'No se pudieron sincronizar los pedidos.';
  }
}
