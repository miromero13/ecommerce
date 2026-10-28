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

  /// Branches of the company that owns the current cart (one cart per company).
  Future<List<PickupBranch>> getPublicBranches() async {
    final cart = await _client.get<Map<String, dynamic>>(
      'cart/current',
      parser: (value) => Map<String, dynamic>.from(value as Map),
    );
    final tenantId = cart.data?['tenant_id'];
    if (tenantId == null) return const [];
    final response = await _client.get<List<PickupBranch>>(
      'branches/public',
      queryParameters: {'tenant_id': tenantId},
      parser: (value) => _parseList(value, PickupBranch.fromJson),
    );
    return response.data ?? const [];
  }

  Future<Map<String, dynamic>> quoteDelivery({
    required String branchId,
    required double latitude,
    required double longitude,
  }) async {
    final response = await _client.post<Map<String, dynamic>>(
      'delivery/quotes',
      data: {'branch_id': branchId, 'latitude': latitude, 'longitude': longitude},
      parser: (value) => Map<String, dynamic>.from(value as Map),
    );
    return {...?response.data, 'message': response.message};
  }

  Future<Map<String, dynamic>> checkoutQr({
    required String pickupBranchId,
    Map<String, dynamic>? delivery,
    int points = 0,
  }) async {
    final response = await _client.post<Map<String, dynamic>>(
      'payments/qr/checkout',
      data: {'pickup_branch_id': pickupBranchId, 'delivery': ?delivery, 'points_to_redeem': points},
      parser: (value) => Map<String, dynamic>.from(value as Map),
    );
    return Map<String, dynamic>.from(response.data!['qr'] as Map);
  }

  /// Delivery orders of the customer, including the PIN shown to the driver.
  Future<Map<String, String>> deliveryPins() async {
    final response = await _client.get<List<dynamic>>('delivery/my-orders', parser: (value) => value as List);
    return {
      for (final row in response.data ?? const [])
        (row as Map)['order_id'].toString(): (row['delivery_pin'] ?? '').toString(),
    };
  }

  Future<StripeCheckoutResult> checkoutStripe({
    required String pickupBranchId,
    Map<String, dynamic>? delivery,
    int points = 0,
  }) async {
    final response = await _client.post<StripeCheckout>(
      'payments/stripe/checkout',
      data: {'pickup_branch_id': pickupBranchId, 'delivery': ?delivery, 'points_to_redeem': points},
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
