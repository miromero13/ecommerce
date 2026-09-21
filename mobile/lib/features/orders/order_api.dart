import '../../core/network/api_client.dart';
import 'order_models.dart';

class OrderApi {
  OrderApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<OrderListResult> getMine() async {
    final response = await _client.get<List<Order>>(
      'orders/me',
      parser: (value) => _parseList(value, Order.fromJson),
    );
    return OrderListResult(
      orders: response.data ?? const [],
      message: response.message,
    );
  }

  Future<OrderResult> getById({required String orderId}) async {
    final response = await _client.get<Order>(
      'orders/$orderId',
      parser: _parseOrder,
    );
    return _orderResult(response.data, response.message);
  }

  Future<List<PickupBranch>> getPublicBranches() async {
    final response = await _client.get<List<PickupBranch>>(
      'branches/public',
      parser: (value) => _parseList(value, PickupBranch.fromJson),
    );
    return response.data ?? const [];
  }

  Future<OrderResult> checkoutCash({required String pickupBranchId}) async {
    final response = await _client.post<Order>(
      'payments/cash/checkout',
      data: {'pickup_branch_id': pickupBranchId},
      parser: _parseOrder,
    );
    return _orderResult(response.data, response.message);
  }

  Future<StripeCheckoutResult> checkoutStripe({
    required String pickupBranchId,
  }) async {
    final response = await _client.post<StripeCheckout>(
      'payments/stripe/checkout',
      data: {'pickup_branch_id': pickupBranchId},
      parser: _parseStripeCheckout,
    );
    final checkout = response.data;
    if (checkout == null) {
      throw const FormatException('La respuesta de Stripe está vacía');
    }
    return StripeCheckoutResult(checkout: checkout, message: response.message);
  }

  Future<StripeCheckoutResult> payOrder({required String orderId}) async {
    final response = await _client.post<StripeCheckout>(
      'payments/stripe/orders/$orderId',
      parser: _parseStripeCheckout,
    );
    final checkout = response.data;
    if (checkout == null) {
      throw const FormatException('La respuesta de Stripe está vacía');
    }
    return StripeCheckoutResult(checkout: checkout, message: response.message);
  }

  static Order _parseOrder(dynamic value) {
    if (value is! Map) {
      throw const FormatException('La respuesta del pedido es inválida');
    }
    return Order.fromJson(Map<String, dynamic>.from(value));
  }

  static StripeCheckout _parseStripeCheckout(dynamic value) {
    if (value is! Map) {
      throw const FormatException('La respuesta de Stripe es inválida');
    }
    return StripeCheckout.fromJson(Map<String, dynamic>.from(value));
  }

  static List<T> _parseList<T>(
    dynamic value,
    T Function(Map<String, dynamic>) parser,
  ) {
    if (value is! List) {
      throw const FormatException('La respuesta de pedidos no es una lista');
    }
    return value
        .map((item) {
          if (item is! Map) {
            throw const FormatException('Un pedido es inválido');
          }
          return parser(Map<String, dynamic>.from(item));
        })
        .toList(growable: false);
  }

  static OrderResult _orderResult(Order? order, String message) {
    if (order == null) {
      throw const FormatException('La respuesta no contiene un pedido');
    }
    return OrderResult(order: order, message: message);
  }
}

class OrderListResult {
  const OrderListResult({required this.orders, required this.message});

  final List<Order> orders;
  final String message;
}

class OrderResult {
  const OrderResult({required this.order, required this.message});

  final Order order;
  final String message;
}

class StripeCheckoutResult {
  const StripeCheckoutResult({required this.checkout, required this.message});

  final StripeCheckout checkout;
  final String message;
}
