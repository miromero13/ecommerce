import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/catalog/catalog_models.dart';

void main() {
  test('parsea producto, precio decimal y variantes en el orden recibido', () {
    final product = Product.fromJson({
      'id': 'product-id',
      'name': 'Producto demo',
      'description': null,
      'price': '110.50',
      'provider_id': null,
      'category_id': 'category-id',
      'season_id': null,
      'collection_id': null,
      'sku': 'SKU-1',
      'image_url': null,
      'image_public_id': 'internal-id',
      'status': 'active',
      'size_id': null,
      'color_id': null,
      'branch_quantity': null,
      'variants': [
        {
          'id': 'variant-2',
          'product_id': 'product-id',
          'sku': 'SKU-2',
          'price': 110.50,
          'size_id': null,
          'color_id': 'color-2',
          'image_url': 'https://example.com/two.jpg',
          'image_public_id': 'internal-two',
          'status': 'active',
          'branch_quantity': 3,
        },
        {
          'id': 'variant-1',
          'product_id': 'product-id',
          'sku': 'SKU-1',
          'price': 110,
          'size_id': 'size-1',
          'color_id': null,
          'image_url': null,
          'image_public_id': null,
          'status': 'active',
          'branch_quantity': null,
        },
      ],
    });

    expect(product.price, 110.50);
    expect(product.status, ProductStatus.active);
    expect(product.variants, hasLength(2));
    expect(product.variants![0].id, 'variant-2');
    expect(product.variants![0].imageUrl, 'https://example.com/two.jpg');
    expect(product.variants![0].branchQuantity, 3);
  });

  test('parsea los modelos públicos de filtros y sucursales', () {
    expect(
      Category.fromJson({'id': 'category-id', 'name': 'Blusas'}).name,
      'Blusas',
    );
    expect(
      CatalogColor.fromJson({
        'id': 'color-id',
        'name': 'Negro',
        'hex_code': '#111111',
      }).hexCode,
      '#111111',
    );
    expect(
      Collection.fromJson({
        'id': 'collection-id',
        'name': 'Urbana',
        'season_id': 'season-id',
      }).seasonId,
      'season-id',
    );
    expect(
      Branch.fromJson({
        'id': 'branch-id',
        'name': 'Central',
        'city': 'La Paz',
        'is_default': true,
        'is_active': true,
      }).isDefault,
      isTrue,
    );
  });
}
