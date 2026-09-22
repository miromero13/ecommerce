enum ProductStatus {
  pending('pending'),
  active('active'),
  inactive('inactive');

  const ProductStatus(this.value);

  final String value;

  static ProductStatus fromJson(Object? value) {
    return values.firstWhere(
      (status) => status.value == value?.toString(),
      orElse: () =>
          throw FormatException('Estado de producto inválido: $value'),
    );
  }
}

class ProductVariant {
  const ProductVariant({
    required this.id,
    required this.productId,
    required this.sku,
      required this.price,
      this.originalPrice,
      this.discountAmount,
    required this.status,
    this.sizeId,
    this.colorId,
    this.imageUrl,
    this.branchQuantity,
  });

  final String id;
  final String productId;
  final String sku;
  final double price;
  final double? originalPrice;
  final double? discountAmount;
  final String? sizeId;
  final String? colorId;
  final String? imageUrl;
  final ProductStatus status;
  final int? branchQuantity;

  factory ProductVariant.fromJson(Map<String, dynamic> json) {
    return ProductVariant(
      id: _requiredString(json, 'id'),
      productId: _requiredString(json, 'product_id'),
      sku: _requiredString(json, 'sku'),
      price: _requiredDouble(json, 'price'),
      originalPrice: _optionalDouble(json, 'original_price'),
      discountAmount: _optionalDouble(json, 'discount_amount'),
      sizeId: _optionalString(json, 'size_id'),
      colorId: _optionalString(json, 'color_id'),
      imageUrl: _optionalString(json, 'image_url'),
      status: ProductStatus.fromJson(json['status']),
      branchQuantity: _optionalInt(json, 'branch_quantity'),
    );
  }
}

class Product {
  const Product({
    required this.id,
    required this.name,
      this.discountType,
      this.discountValue,
    required this.categoryId,
    this.description,
    this.providerId,
    this.collectionId,
    this.sku,
    this.imageUrl,
    this.status,
    this.sizeId,
    this.colorId,
    this.branchQuantity,
    this.variants,
  });

  final String id;
  final String name;
  final String? description;
  final String? discountType;
  final double? discountValue;
  final String? providerId;
  final String categoryId;
  final String? collectionId;
  final String? sku;
  final String? imageUrl;
  final ProductStatus? status;
  final String? sizeId;
  final String? colorId;
  final int? branchQuantity;
  final List<ProductVariant>? variants;

  factory Product.fromJson(Map<String, dynamic> json) {
    final rawVariants = json['variants'];
    return Product(
      id: _requiredString(json, 'id'),
      name: _requiredString(json, 'name'),
      description: _optionalString(json, 'description'),
      discountType: _optionalString(json, 'discount_type'),
      discountValue: _optionalDouble(json, 'discount_value'),
      providerId: _optionalString(json, 'provider_id'),
      categoryId: _requiredString(json, 'category_id'),
      collectionId: _optionalString(json, 'collection_id'),
      sku: _optionalString(json, 'sku'),
      imageUrl: _optionalString(json, 'image_url'),
      status: json['status'] == null
          ? null
          : ProductStatus.fromJson(json['status']),
      sizeId: _optionalString(json, 'size_id'),
      colorId: _optionalString(json, 'color_id'),
      branchQuantity: _optionalInt(json, 'branch_quantity'),
      variants: rawVariants == null
          ? null
          : _parseList(rawVariants, ProductVariant.fromJson),
    );
  }
}

class CollaborativeRecommendation {
  const CollaborativeRecommendation({required this.productId, this.score});

  final String productId;
  final double? score;

  factory CollaborativeRecommendation.fromJson(Map<String, dynamic> json) {
    return CollaborativeRecommendation(
      productId: _requiredString(json, 'product_id'),
      score: _optionalDouble(json, 'score'),
    );
  }
}

class CollaborativeRecommendations {
  const CollaborativeRecommendations({required this.recommendations});

  final List<CollaborativeRecommendation> recommendations;

  factory CollaborativeRecommendations.fromJson(Map<String, dynamic> json) {
    final rawRecommendations = json['recommendations'];
    if (rawRecommendations is! List) {
      throw const FormatException('Las recomendaciones son inválidas');
    }
    return CollaborativeRecommendations(
      recommendations: _parseList(
        rawRecommendations,
        CollaborativeRecommendation.fromJson,
      ),
    );
  }
}

class Category {
  const Category({required this.id, required this.name});

  final String id;
  final String name;

  factory Category.fromJson(Map<String, dynamic> json) {
    return Category(
      id: _requiredString(json, 'id'),
      name: _requiredString(json, 'name'),
    );
  }
}

class Size {
  const Size({required this.id, required this.name});

  final String id;
  final String name;

  factory Size.fromJson(Map<String, dynamic> json) {
    return Size(
      id: _requiredString(json, 'id'),
      name: _requiredString(json, 'name'),
    );
  }
}

class CatalogColor {
  const CatalogColor({required this.id, required this.name, this.hexCode});

  final String id;
  final String name;
  final String? hexCode;

  factory CatalogColor.fromJson(Map<String, dynamic> json) {
    return CatalogColor(
      id: _requiredString(json, 'id'),
      name: _requiredString(json, 'name'),
      hexCode: _optionalString(json, 'hex_code'),
    );
  }
}

class Season {
  const Season({required this.id, required this.name});

  final String id;
  final String name;

  factory Season.fromJson(Map<String, dynamic> json) {
    return Season(
      id: _requiredString(json, 'id'),
      name: _requiredString(json, 'name'),
    );
  }
}

class Collection {
  const Collection({required this.id, required this.name, this.seasonId});

  final String id;
  final String name;
  final String? seasonId;

  factory Collection.fromJson(Map<String, dynamic> json) {
    return Collection(
      id: _requiredString(json, 'id'),
      name: _requiredString(json, 'name'),
      seasonId: _optionalString(json, 'season_id'),
    );
  }
}

class Branch {
  const Branch({
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

  factory Branch.fromJson(Map<String, dynamic> json) {
    return Branch(
      id: _requiredString(json, 'id'),
      name: _requiredString(json, 'name'),
      city: _requiredString(json, 'city'),
      isDefault: _requiredBool(json, 'is_default'),
      isActive: _requiredBool(json, 'is_active'),
    );
  }
}

List<T> _parseList<T>(dynamic value, T Function(Map<String, dynamic>) parser) {
  if (value is! List) {
    throw const FormatException('La respuesta del catálogo no es una lista');
  }

  return value
      .map((item) {
        if (item is! Map) {
          throw const FormatException('Un elemento del catálogo es inválido');
        }
        return parser(Map<String, dynamic>.from(item));
      })
      .toList(growable: false);
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

double _requiredDouble(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is num) {
    return value.toDouble();
  }
  final parsed = double.tryParse(value?.toString() ?? '');
  if (parsed == null) {
    throw FormatException('$key inválido');
  }
  return parsed;
}

double? _optionalDouble(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null) return null;
  if (value is num) return value.toDouble();
  return double.tryParse(value.toString());
}

int? _optionalInt(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null) {
    return null;
  }
  if (value is num) {
    return value.toInt();
  }
  return int.tryParse(value.toString());
}

bool _requiredBool(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is! bool) {
    throw FormatException('$key inválido');
  }
  return value;
}
