enum CartStatus {
  active('active'),
  checkedOut('checked_out'),
  cancelled('cancelled');

  const CartStatus(this.value);

  final String value;

  static CartStatus fromJson(Object? value) {
    return values.firstWhere(
      (status) => status.value == value?.toString(),
      orElse: () => throw FormatException('Estado de carrito inválido: $value'),
    );
  }
}

class CartItem {
  const CartItem({
    required this.id,
    required this.cartId,
    required this.variantId,
    required this.quantity,
    required this.unitPrice,
    this.originalUnitPrice,
    this.discountAmount,
    required this.lineTotal,
    required this.productId,
    required this.productName,
    required this.variantSku,
    this.sizeId,
    this.colorId,
    this.sizeName,
    this.colorName,
    this.imageUrl,
  });

  final String id;
  final String cartId;
  final String variantId;
  final int quantity;
  final double unitPrice;
  final double? originalUnitPrice;
  final double? discountAmount;
  final double lineTotal;
  final String productId;
  final String productName;
  final String variantSku;
  final String? sizeId;
  final String? colorId;
  final String? sizeName;
  final String? colorName;
  final String? imageUrl;

  factory CartItem.fromJson(Map<String, dynamic> json) {
    return CartItem(
      id: _requiredString(json, 'id'),
      cartId: _requiredString(json, 'cart_id'),
      variantId: _requiredString(json, 'variant_id'),
      quantity: _requiredInt(json, 'quantity'),
      unitPrice: _requiredDouble(json, 'unit_price'),
      originalUnitPrice: _optionalDouble(json, 'original_unit_price'),
      discountAmount: _optionalDouble(json, 'discount_amount'),
      lineTotal: _requiredDouble(json, 'line_total'),
      productId: _requiredString(json, 'product_id'),
      productName: _requiredString(json, 'product_name'),
      variantSku: _requiredString(json, 'variant_sku'),
      sizeId: _optionalString(json, 'size_id'),
      colorId: _optionalString(json, 'color_id'),
      sizeName: _optionalString(json, 'size_name'),
      colorName: _optionalString(json, 'color_name'),
      imageUrl: _optionalString(json, 'image_url'),
    );
  }
}

class Cart {
  const Cart({
    required this.id,
    required this.userId,
    required this.status,
    required this.subtotal,
    required this.discountAmount,
    required this.totalAmount,
    required this.itemCount,
    required this.createdAt,
    required this.items,
    this.promotionCodeId,
    this.promotionCode,
    this.updatedAt,
  });

  final String id;
  final String userId;
  final CartStatus status;
  final double subtotal;
  final double discountAmount;
  final double totalAmount;
  final int itemCount;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final List<CartItem> items;
  final String? promotionCodeId;
  final String? promotionCode;

  factory Cart.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'];
    if (rawItems is! List) {
      throw const FormatException('Los ítems del carrito son inválidos');
    }

    return Cart(
      id: _requiredString(json, 'id'),
      userId: _requiredString(json, 'user_id'),
      status: CartStatus.fromJson(json['status']),
      subtotal: _requiredDouble(json, 'subtotal'),
      discountAmount: _requiredDouble(json, 'discount_amount'),
      totalAmount: _requiredDouble(json, 'total_amount'),
      itemCount: _requiredInt(json, 'item_count'),
      createdAt: _requiredDateTime(json, 'created_at'),
      updatedAt: _optionalDateTime(json, 'updated_at'),
      promotionCodeId: _optionalString(json, 'promotion_code_id'),
      promotionCode: _optionalString(json, 'promotion_code'),
      items: rawItems
          .map((item) {
            if (item is! Map) {
              throw const FormatException('Un ítem del carrito es inválido');
            }
            return CartItem.fromJson(Map<String, dynamic>.from(item));
          })
          .toList(growable: false),
    );
  }
}

class CartOperationResult {
  const CartOperationResult({required this.cart, required this.message});

  final Cart cart;
  final String message;
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

double? _optionalDouble(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null) return null;
  if (value is num) return value.toDouble();
  return double.tryParse(value.toString());
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
