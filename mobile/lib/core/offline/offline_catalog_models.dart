class OfflineVariant {
  final String id;
  final String sku;
  final double price;
  final String? size;
  final String? sizeId;
  final String? color;
  final String? colorHex;
  final String? colorId;
  final String? imageUrl;
  final int availableStock;

  const OfflineVariant({
    required this.id,
    required this.sku,
    required this.price,
    this.size,
    this.sizeId,
    this.color,
    this.colorHex,
    this.colorId,
    this.imageUrl,
    required this.availableStock,
  });

  factory OfflineVariant.fromJson(Map<String, dynamic> json) {
    return OfflineVariant(
      id: json['id'] as String? ?? '',
      sku: json['sku'] as String? ?? '',
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
      size: json['size'] as String?,
      sizeId: json['size_id'] as String?,
      color: json['color'] as String?,
      colorHex: json['color_hex'] as String?,
      colorId: json['color_id'] as String?,
      imageUrl: json['image_url'] as String?,
      availableStock: (json['available_stock'] as num?)?.toInt() ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'sku': sku,
      'price': price,
      'size': size,
      'size_id': sizeId,
      'color': color,
      'color_hex': colorHex,
      'color_id': colorId,
      'image_url': imageUrl,
      'available_stock': availableStock,
    };
  }
}

class OfflineCatalogProduct {
  final String id;
  final String tenantId;
  final String name;
  final String description;
  final String? categoryId;
  final String category;
  final String? discountType;
  final double? discountValue;
  final List<OfflineVariant> variants;
  final String syncedAt;

  const OfflineCatalogProduct({
    required this.id,
    required this.tenantId,
    required this.name,
    required this.description,
    this.categoryId,
    required this.category,
    this.discountType,
    this.discountValue,
    required this.variants,
    required this.syncedAt,
  });

  factory OfflineCatalogProduct.fromJson(Map<String, dynamic> json) {
    final rawVariants = json['variants'] as List<dynamic>? ?? [];
    return OfflineCatalogProduct(
      id: json['id'] as String? ?? '',
      tenantId: json['tenant_id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String? ?? '',
      categoryId: json['category_id'] as String?,
      category: json['category'] as String? ?? 'General',
      discountType: json['discount_type'] as String?,
      discountValue: (json['discount_value'] as num?)?.toDouble(),
      variants: rawVariants
          .whereType<Map<String, dynamic>>()
          .map((v) => OfflineVariant.fromJson(v))
          .toList(),
      syncedAt: json['synced_at'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tenant_id': tenantId,
      'name': name,
      'description': description,
      'category_id': categoryId,
      'category': category,
      'discount_type': discountType,
      'discount_value': discountValue,
      'variants': variants.map((v) => v.toJson()).toList(),
      'synced_at': syncedAt,
    };
  }
}
