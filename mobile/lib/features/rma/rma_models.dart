class SameProductVariant {
  const SameProductVariant({
    required this.variantId,
    required this.sku,
    this.sizeName,
    this.colorName,
    required this.stock,
  });

  final String variantId;
  final String sku;
  final String? sizeName;
  final String? colorName;
  final int stock;

  String get label => '${sizeName ?? 'Única'} · ${colorName ?? 'Estándar'} (${stock > 0 ? '$stock disp.' : 'Sin stock'})';

  factory SameProductVariant.fromJson(Map<String, dynamic> json) {
    return SameProductVariant(
      variantId: (json['variant_id'] ?? '').toString(),
      sku: (json['sku'] ?? '').toString(),
      sizeName: json['size_name'] as String?,
      colorName: json['color_name'] as String?,
      stock: int.tryParse('${json['stock'] ?? 0}') ?? 0,
    );
  }
}

class EligibleOrderItem {
  const EligibleOrderItem({
    required this.orderItemId,
    required this.productId,
    required this.productName,
    required this.variantId,
    required this.sku,
    this.sizeName,
    this.colorName,
    required this.unitPrice,
    required this.quantity,
    this.imageUrl,
    required this.eligibleForRma,
    this.ineligibleReason,
    required this.sameProductVariants,
  });

  final String orderItemId;
  final String productId;
  final String productName;
  final String variantId;
  final String sku;
  final String? sizeName;
  final String? colorName;
  final double unitPrice;
  final int quantity;
  final String? imageUrl;
  final bool eligibleForRma;
  final String? ineligibleReason;
  final List<SameProductVariant> sameProductVariants;

  factory EligibleOrderItem.fromJson(Map<String, dynamic> json) {
    final rawVariants = json['same_product_variants'];
    return EligibleOrderItem(
      orderItemId: (json['order_item_id'] ?? '').toString(),
      productId: (json['product_id'] ?? '').toString(),
      productName: (json['product_name'] ?? '').toString(),
      variantId: (json['variant_id'] ?? '').toString(),
      sku: (json['sku'] ?? '').toString(),
      sizeName: json['size_name'] as String?,
      colorName: json['color_name'] as String?,
      unitPrice: double.tryParse('${json['unit_price'] ?? 0}') ?? 0,
      quantity: int.tryParse('${json['quantity'] ?? 1}') ?? 1,
      imageUrl: json['image_url'] as String?,
      eligibleForRma: json['eligible_for_rma'] as bool? ?? true,
      ineligibleReason: json['ineligible_reason'] as String?,
      sameProductVariants: (rawVariants is List)
          ? rawVariants
              .whereType<Map<String, dynamic>>()
              .map(SameProductVariant.fromJson)
              .toList(growable: false)
          : const [],
    );
  }
}

class EligibleOrder {
  const EligibleOrder({
    required this.orderId,
    required this.orderNumber,
    this.deliveredAt,
    required this.createdAt,
    required this.daysSinceDelivery,
    required this.items,
  });

  final String orderId;
  final String orderNumber;
  final DateTime? deliveredAt;
  final DateTime createdAt;
  final int daysSinceDelivery;
  final List<EligibleOrderItem> items;

  factory EligibleOrder.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'];
    return EligibleOrder(
      orderId: (json['order_id'] ?? '').toString(),
      orderNumber: (json['order_number'] ?? '').toString(),
      deliveredAt: json['delivered_at'] != null
          ? DateTime.tryParse(json['delivered_at'].toString())
          : null,
      createdAt:
          DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now(),
      daysSinceDelivery: int.tryParse('${json['days_since_delivery'] ?? 0}') ?? 0,
      items: (rawItems is List)
          ? rawItems
              .whereType<Map<String, dynamic>>()
              .map(EligibleOrderItem.fromJson)
              .toList(growable: false)
          : const [],
    );
  }
}

class RmaItem {
  const RmaItem({
    required this.id,
    required this.productName,
    required this.originalSku,
    this.originalSize,
    this.originalColor,
    required this.unitPrice,
    required this.quantity,
    this.imageUrl,
    required this.reason,
    required this.preferredResolution,
    this.requestedVariantLabel,
    this.customerNotes,
    this.inspectionNotes,
    this.itemCondition,
    required this.status,
    this.quarantineRecord,
    this.refundAmount,
  });

  final String id;
  final String productName;
  final String originalSku;
  final String? originalSize;
  final String? originalColor;
  final double unitPrice;
  final int quantity;
  final String? imageUrl;
  final String reason;
  final String preferredResolution;
  final String? requestedVariantLabel;
  final String? customerNotes;
  final String? inspectionNotes;
  final String? itemCondition;
  final String status;
  final String? quarantineRecord;
  final double? refundAmount;

  String get reasonLabel {
    return switch (reason) {
      'size_change' => 'Cambio de talla',
      'color_change' => 'Cambio de color',
      'factory_defect' => 'Falla / Defecto de fábrica',
      'not_as_expected' => 'No es lo que esperaba',
      _ => reason,
    };
  }

  String get resolutionLabel {
    return switch (preferredResolution) {
      'exchange' => 'Cambio por otra prenda',
      'store_credit' => 'Saldo en Billetera Digital',
      _ => preferredResolution,
    };
  }

  String get statusLabel {
    return switch (status) {
      'pending_inspection' => 'Pendiente de inspección',
      'approved' || 'accepted_restock' => 'Aprobado (Reingreso)',
      'accepted_scrap' => 'Aprobado (Falla de fábrica / Merma)',
      'rejected' => 'Rechazado',
      _ => status,
    };
  }

  factory RmaItem.fromJson(Map<String, dynamic> json) {
    return RmaItem(
      id: (json['id'] ?? '').toString(),
      productName: (json['product_name'] ?? '').toString(),
      originalSku: (json['original_sku'] ?? '').toString(),
      originalSize: json['original_size'] as String?,
      originalColor: json['original_color'] as String?,
      unitPrice: double.tryParse('${json['unit_price'] ?? 0}') ?? 0,
      quantity: int.tryParse('${json['quantity'] ?? 1}') ?? 1,
      imageUrl: json['image_url'] as String?,
      reason: (json['reason'] ?? '').toString(),
      preferredResolution: (json['preferred_resolution'] ?? '').toString(),
      requestedVariantLabel: json['requested_variant_label'] as String?,
      customerNotes: json['customer_notes'] as String?,
      inspectionNotes: json['inspection_notes'] as String?,
      itemCondition: json['item_condition'] as String?,
      status: (json['status'] ?? '').toString(),
      quarantineRecord: json['quarantine_record'] as String?,
      refundAmount: json['refund_amount'] != null
          ? double.tryParse('${json['refund_amount']}')
          : null,
    );
  }
}

class RmaRequest {
  const RmaRequest({
    required this.id,
    required this.rmaNumber,
    required this.orderId,
    required this.orderNumber,
    required this.status,
    this.customerNotes,
    required this.pdfUrl,
    required this.createdAt,
    required this.items,
  });

  final String id;
  final String rmaNumber;
  final String orderId;
  final String orderNumber;
  final String status;
  final String? customerNotes;
  final String pdfUrl;
  final DateTime createdAt;
  final List<RmaItem> items;

  String get statusLabel {
    return switch (status) {
      'pending_inspection' => 'Pendiente en sucursal',
      'approved' => 'Aprobado',
      'partially_approved' => 'Parcialmente aprobado',
      'rejected' => 'Rechazado',
      'completed' => 'Completado / Resuelto',
      _ => status,
    };
  }

  factory RmaRequest.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'];
    return RmaRequest(
      id: (json['id'] ?? '').toString(),
      rmaNumber: (json['rma_number'] ?? '').toString(),
      orderId: (json['order_id'] ?? '').toString(),
      orderNumber: (json['order_number'] ?? '').toString(),
      status: (json['status'] ?? 'pending_inspection').toString(),
      customerNotes: json['customer_notes'] as String?,
      pdfUrl: (json['pdf_url'] ?? '').toString(),
      createdAt:
          DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now(),
      items: (rawItems is List)
          ? rawItems
              .whereType<Map<String, dynamic>>()
              .map(RmaItem.fromJson)
              .toList(growable: false)
          : const [],
    );
  }
}
