class DeliveryOrder {
  const DeliveryOrder({
    required this.orderId,
    required this.tenantName,
    this.branchName,
    this.branchCity,
    this.clientName,
    required this.address,
    this.reference,
    this.distanceKm,
    required this.shippingCost,
    required this.totalAmount,
    required this.currency,
    required this.status,
    this.driverName,
    this.deliveredAt,
    required this.createdAt,
    this.deliveryPin,
  });

  final String orderId;
  final String tenantName;
  final String? branchName;
  final String? branchCity;
  final String? clientName;
  final String address;
  final String? reference;
  final double? distanceKm;
  final double shippingCost;
  final double totalAmount;
  final String currency;
  final String status;
  final String? driverName;
  final DateTime? deliveredAt;
  final DateTime createdAt;
  final String? deliveryPin;

  bool get isActive =>
      status == 'in_transit' ||
      status == 'ready_for_pickup' ||
      status == 'pending_pickup';

  String get statusLabel {
    return switch (status) {
      'in_transit' => 'En camino',
      'delivered' => 'Entregado',
      'ready_for_pickup' => 'Listo para despacho',
      'pending_pickup' => 'En preparación',
      'cancelled' => 'Cancelado',
      _ => status,
    };
  }

  factory DeliveryOrder.fromJson(Map<String, dynamic> json) {
    return DeliveryOrder(
      orderId: (json['order_id'] ?? '').toString(),
      tenantName: (json['tenant_name'] ?? '').toString(),
      branchName: json['branch_name'] as String?,
      branchCity: json['branch_city'] as String?,
      clientName: json['client_name'] as String?,
      address: (json['address'] ?? '').toString(),
      reference: json['reference'] as String?,
      distanceKm: json['distance_km'] != null
          ? double.tryParse('${json['distance_km']}')
          : null,
      shippingCost: double.tryParse('${json['shipping_cost'] ?? 0}') ?? 0,
      totalAmount: double.tryParse('${json['total_amount'] ?? 0}') ?? 0,
      currency: (json['currency'] ?? 'BOB').toString(),
      status: (json['status'] ?? '').toString(),
      driverName: json['driver_name'] as String?,
      deliveredAt: json['delivered_at'] != null
          ? DateTime.tryParse(json['delivered_at'].toString())
          : null,
      createdAt:
          DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now(),
      deliveryPin: json['delivery_pin'] as String?,
    );
  }
}
