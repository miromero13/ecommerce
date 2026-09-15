enum ReservationStatus {
  pending('pending'),
  confirmed('confirmed'),
  attended('attended'),
  purchasePending('purchase_pending'),
  sold('sold'),
  notSold('not_sold'),
  cancelled('cancelled'),
  expired('expired');

  const ReservationStatus(this.value);

  final String value;

  static ReservationStatus fromJson(Object? value) {
    return values.firstWhere(
      (status) => status.value == value?.toString(),
      orElse: () => throw FormatException('Estado de reserva inválido: $value'),
    );
  }
}

class ReservationItem {
  const ReservationItem({
    required this.id,
    required this.reservationId,
    required this.variantId,
    required this.quantity,
    required this.unitPrice,
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
  final String reservationId;
  final String variantId;
  final int quantity;
  final double unitPrice;
  final double lineTotal;
  final String productId;
  final String productName;
  final String variantSku;
  final String? sizeId;
  final String? colorId;
  final String? sizeName;
  final String? colorName;
  final String? imageUrl;

  factory ReservationItem.fromJson(Map<String, dynamic> json) {
    return ReservationItem(
      id: _requiredString(json, 'id'),
      reservationId: _requiredString(json, 'reservation_id'),
      variantId: _requiredString(json, 'variant_id'),
      quantity: _requiredInt(json, 'quantity'),
      unitPrice: _requiredDouble(json, 'unit_price'),
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

class Reservation {
  const Reservation({
    required this.id,
    required this.branchId,
    required this.branchName,
    required this.userId,
    required this.visitDate,
    required this.expiresAt,
    required this.status,
    required this.totalAmount,
    required this.itemCount,
    required this.createdAt,
    required this.items,
    this.updatedAt,
    this.cartId,
  });

  final String id;
  final String branchId;
  final String branchName;
  final String userId;
  final DateTime visitDate;
  final DateTime expiresAt;
  final ReservationStatus status;
  final double totalAmount;
  final int itemCount;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final String? cartId;
  final List<ReservationItem> items;

  bool get canCancel =>
      status == ReservationStatus.pending ||
      status == ReservationStatus.confirmed;

  factory Reservation.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'];
    if (rawItems is! List) {
      throw const FormatException('Los ítems de la reserva son inválidos');
    }

    return Reservation(
      id: _requiredString(json, 'id'),
      branchId: _requiredString(json, 'branch_id'),
      branchName: _requiredString(json, 'branch_name'),
      userId: _requiredString(json, 'user_id'),
      visitDate: _requiredDate(json, 'visit_date'),
      expiresAt: _requiredDate(json, 'expires_at'),
      status: ReservationStatus.fromJson(json['status']),
      totalAmount: _requiredDouble(json, 'total_amount'),
      itemCount: _requiredInt(json, 'item_count'),
      createdAt: _requiredDateTime(json, 'created_at'),
      updatedAt: _optionalDateTime(json, 'updated_at'),
      cartId: _optionalString(json, 'cart_id'),
      items: rawItems
          .map((item) {
            if (item is! Map) {
              throw const FormatException('Un ítem de reserva es inválido');
            }
            return ReservationItem.fromJson(Map<String, dynamic>.from(item));
          })
          .toList(growable: false),
    );
  }
}

class ReservationDraftItem {
  const ReservationDraftItem({
    required this.variantId,
    required this.quantity,
    this.productName,
    this.variantSku,
    this.imageUrl,
  });

  final String variantId;
  final int quantity;
  final String? productName;
  final String? variantSku;
  final String? imageUrl;

  Map<String, dynamic> toJson() {
    return {'variant_id': variantId, 'quantity': quantity};
  }
}

class ReservationArguments {
  const ReservationArguments({this.items = const []});

  final List<ReservationDraftItem> items;
}

String formatReservationDate(DateTime date) {
  final year = date.year.toString().padLeft(4, '0');
  final month = date.month.toString().padLeft(2, '0');
  final day = date.day.toString().padLeft(2, '0');
  return '$year-$month-$day';
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

DateTime _requiredDate(Map<String, dynamic> json, String key) {
  final value = DateTime.tryParse(json[key]?.toString() ?? '');
  if (value == null) throw FormatException('$key inválido');
  return DateTime(value.year, value.month, value.day);
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
