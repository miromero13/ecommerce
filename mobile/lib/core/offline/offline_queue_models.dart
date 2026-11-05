class OfflineOrderItem {
  final String variantId;
  final String productName;
  final String variantSku;
  final double unitPrice;
  final int quantity;
  final double subtotal;

  const OfflineOrderItem({
    required this.variantId,
    required this.productName,
    required this.variantSku,
    required this.unitPrice,
    required this.quantity,
    required this.subtotal,
  });

  factory OfflineOrderItem.fromJson(Map<String, dynamic> json) {
    return OfflineOrderItem(
      variantId: json['variant_id'] as String? ?? '',
      productName: json['product_name'] as String? ?? '',
      variantSku: json['variant_sku'] as String? ?? '',
      unitPrice: (json['unit_price'] as num?)?.toDouble() ?? 0.0,
      quantity: (json['quantity'] as num?)?.toInt() ?? 1,
      subtotal: (json['subtotal'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'variant_id': variantId,
      'product_name': productName,
      'variant_sku': variantSku,
      'unit_price': unitPrice,
      'quantity': quantity,
      'subtotal': subtotal,
    };
  }
}

class OfflineOperation {
  final String operationId;
  final String receiptNumber;
  final String type; // 'cash_sale' | 'reservation'
  final String status; // 'local_pending' | 'syncing' | 'synced' | 'conflict_rejected'
  final String createdAt;
  final String? tenantId;
  final String? branchId;
  final String? customerName;
  final String? customerEmail;
  final double subtotal;
  final double discount;
  final double total;
  final double? cashReceived;
  final double? changeReturned;
  final String? notes;
  final String? syncError;
  final List<OfflineOrderItem> items;

  const OfflineOperation({
    required this.operationId,
    required this.receiptNumber,
    required this.type,
    required this.status,
    required this.createdAt,
    this.tenantId,
    this.branchId,
    this.customerName,
    this.customerEmail,
    required this.subtotal,
    required this.discount,
    required this.total,
    this.cashReceived,
    this.changeReturned,
    this.notes,
    this.syncError,
    required this.items,
  });

  factory OfflineOperation.fromJson(Map<String, dynamic> json) {
    final rawItems = (json['items'] as List<dynamic>?) ?? [];
    return OfflineOperation(
      operationId: json['operation_id'] as String? ?? '',
      receiptNumber: json['receipt_number'] as String? ?? '',
      type: json['type'] as String? ?? 'cash_sale',
      status: json['status'] as String? ?? 'local_pending',
      createdAt: json['created_at'] as String? ?? '',
      tenantId: json['tenant_id'] as String?,
      branchId: json['branch_id'] as String?,
      customerName: json['customer_name'] as String?,
      customerEmail: json['customer_email'] as String?,
      subtotal: (json['subtotal'] as num?)?.toDouble() ?? 0.0,
      discount: (json['discount'] as num?)?.toDouble() ?? 0.0,
      total: (json['total'] as num?)?.toDouble() ?? 0.0,
      cashReceived: (json['cash_received'] as num?)?.toDouble(),
      changeReturned: (json['change_returned'] as num?)?.toDouble(),
      notes: json['notes'] as String?,
      syncError: json['sync_error'] as String?,
      items: rawItems
          .whereType<Map<String, dynamic>>()
          .map((i) => OfflineOrderItem.fromJson(i))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'operation_id': operationId,
      'receipt_number': receiptNumber,
      'type': type,
      'status': status,
      'created_at': createdAt,
      'tenant_id': tenantId,
      'branch_id': branchId,
      'customer_name': customerName,
      'customer_email': customerEmail,
      'subtotal': subtotal,
      'discount': discount,
      'total': total,
      'cash_received': cashReceived,
      'change_returned': changeReturned,
      'notes': notes,
      'sync_error': syncError,
      'items': items.map((i) => i.toJson()).toList(),
    };
  }
}
