enum OrderStatus {
  pending('pending'),
  paid('paid'),
  failed('failed'),
  cancelled('cancelled');

  const OrderStatus(this.value);

  final String value;

  static OrderStatus fromJson(Object? value) {
    return values.firstWhere(
      (status) => status.value == value?.toString(),
      orElse: () => throw FormatException('Estado de pedido inválido: $value'),
    );
  }
}

enum PaymentMethod {
  cash('cash'),
  stripe('stripe');

  const PaymentMethod(this.value);

  final String value;

  static PaymentMethod fromJson(Object? value) {
    return values.firstWhere(
      (method) => method.value == value?.toString(),
      orElse: () => throw FormatException('Método de pago inválido: $value'),
    );
  }
}

enum PaymentStatus {
  pending('pending'),
  paid('paid'),
  failed('failed');

  const PaymentStatus(this.value);

  final String value;

  static PaymentStatus fromJson(Object? value) {
    return values.firstWhere(
      (status) => status.value == value?.toString(),
      orElse: () => throw FormatException('Estado de pago inválido: $value'),
    );
  }
}

enum FulfillmentStatus {
  pendingPickup('pending_pickup'),
  readyForPickup('ready_for_pickup'),
  collected('collected'),
  expired('expired'),
  cancelled('cancelled');

  const FulfillmentStatus(this.value);

  final String value;

  static FulfillmentStatus fromJson(Object? value) {
    return values.firstWhere(
      (status) => status.value == value?.toString(),
      orElse: () => FulfillmentStatus.pendingPickup,
    );
  }
}

class OrderItem {
  const OrderItem({
    required this.id,
    required this.orderId,
    required this.variantId,
    required this.quantity,
    required this.unitPrice,
    required this.lineTotal,
    required this.productId,
    required this.productName,
    required this.variantSku,
    this.sizeName,
    this.colorName,
    this.imageUrl,
  });

  final String id;
  final String orderId;
  final String variantId;
  final int quantity;
  final double unitPrice;
  final double lineTotal;
  final String productId;
  final String productName;
  final String variantSku;
  final String? sizeName;
  final String? colorName;
  final String? imageUrl;

  factory OrderItem.fromJson(Map<String, dynamic> json) {
    return OrderItem(
      id: _requiredString(json, 'id'),
      orderId: _requiredString(json, 'order_id'),
      variantId: _requiredString(json, 'variant_id'),
      quantity: _requiredInt(json, 'quantity'),
      unitPrice: _requiredDouble(json, 'unit_price'),
      lineTotal: _requiredDouble(json, 'line_total'),
      productId: _requiredString(json, 'product_id'),
      productName: _requiredString(json, 'product_name'),
      variantSku: _requiredString(json, 'variant_sku'),
      sizeName: _optionalString(json, 'size_name'),
      colorName: _optionalString(json, 'color_name'),
      imageUrl: _optionalString(json, 'image_url'),
    );
  }
}

class Order {
  const Order({
    required this.id,
    required this.userId,
    required this.status,
    required this.paymentMethod,
    required this.paymentStatus,
    this.fulfillmentStatus = FulfillmentStatus.pendingPickup,
    required this.subtotal,
    required this.discountAmount,
    required this.totalAmount,
    required this.currency,
    required this.createdAt,
    required this.items,
    this.stripePaymentIntentId,
    this.cashReference,
    this.pickupBranchId,
    this.pickupExpiresAt,
    this.pickupCode,
    this.updatedAt,
  });

  final String id;
  final String userId;
  final OrderStatus status;
  final PaymentMethod paymentMethod;
  final PaymentStatus paymentStatus;
  final FulfillmentStatus fulfillmentStatus;
  final double subtotal;
  final double discountAmount;
  final double totalAmount;
  final String currency;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final String? stripePaymentIntentId;
  final String? cashReference;
  final String? pickupBranchId;
  final DateTime? pickupExpiresAt;
  final String? pickupCode;
  final List<OrderItem> items;

  factory Order.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'];
    if (rawItems is! List) {
      throw const FormatException('Los ítems del pedido son inválidos');
    }

    return Order(
      id: _requiredString(json, 'id'),
      userId: _requiredString(json, 'user_id'),
      status: OrderStatus.fromJson(json['status']),
      paymentMethod: PaymentMethod.fromJson(json['payment_method']),
      paymentStatus: PaymentStatus.fromJson(json['payment_status']),
      fulfillmentStatus: FulfillmentStatus.fromJson(json['fulfillment_status']),
      subtotal: _requiredDouble(json, 'subtotal'),
      discountAmount: _requiredDouble(json, 'discount_amount'),
      totalAmount: _requiredDouble(json, 'total_amount'),
      currency: _requiredString(json, 'currency'),
      createdAt: _requiredDateTime(json, 'created_at'),
      updatedAt: _optionalDateTime(json, 'updated_at'),
      stripePaymentIntentId: _optionalString(json, 'stripe_payment_intent_id'),
      cashReference: _optionalString(json, 'cash_reference'),
      pickupBranchId: _optionalString(json, 'pickup_branch_id'),
      pickupExpiresAt: _optionalDateTime(json, 'pickup_expires_at'),
      pickupCode: _optionalString(json, 'pickup_code'),
      items: rawItems
          .map((item) {
            if (item is! Map) {
              throw const FormatException('Un ítem de pedido es inválido');
            }
            return OrderItem.fromJson(Map<String, dynamic>.from(item));
          })
          .toList(growable: false),
    );
  }
}

class PickupBranch {
  const PickupBranch({
    required this.id,
    required this.name,
    required this.city,
    required this.isDefault,
    required this.isActive,
  });

  final String id;
  final String name;
  final String city;
  final bool isDefault;
  final bool isActive;

  factory PickupBranch.fromJson(Map<String, dynamic> json) {
    return PickupBranch(
      id: _requiredString(json, 'id'),
      name: _requiredString(json, 'name'),
      city: _requiredString(json, 'city'),
      isDefault: json['is_default'] == true,
      isActive: json['is_active'] == true,
    );
  }
}

class StripeCheckout {
  const StripeCheckout({
    required this.orderId,
    required this.clientSecret,
    required this.paymentIntentId,
  });

  final String orderId;
  final String clientSecret;
  final String paymentIntentId;

  factory StripeCheckout.fromJson(Map<String, dynamic> json) {
    return StripeCheckout(
      orderId: _requiredString(json, 'order_id'),
      clientSecret: _requiredString(json, 'client_secret'),
      paymentIntentId: _requiredString(json, 'payment_intent_id'),
    );
  }
}

String _requiredString(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null || value.toString().trim().isEmpty) {
    throw FormatException('$key inválido');
  }
  return value.toString();
}

String? _optionalString(Map<String, dynamic> json, String key) {
  return json[key]?.toString();
}

int _requiredInt(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is num) return value.toInt();
  final parsed = int.tryParse(value?.toString() ?? '');
  if (parsed == null) throw FormatException('$key inválido');
  return parsed;
}

double _requiredDouble(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is num) return value.toDouble();
  final parsed = double.tryParse(value?.toString() ?? '');
  if (parsed == null) throw FormatException('$key inválido');
  return parsed;
}

DateTime _requiredDateTime(Map<String, dynamic> json, String key) {
  final value = DateTime.tryParse(json[key]?.toString() ?? '');
  if (value == null) throw FormatException('$key inválido');
  return value;
}

DateTime? _optionalDateTime(Map<String, dynamic> json, String key) {
  final rawValue = json[key];
  if (rawValue == null) return null;
  final value = DateTime.tryParse(rawValue.toString());
  if (value == null) throw FormatException('$key inválido');
  return value;
}
