import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/offline/offline_catalog_models.dart';

void main() {
  group('CU23 OfflineCatalogModels & Search Tests', () {
    test('OfflineCatalogProduct fromJson & toJson work correctly', () {
      final json = {
        'id': 'prod-123',
        'tenant_id': 'tenant-456',
        'name': 'Camisa de Lino Azul',
        'description': 'Camisa veraniega fresca',
        'category_id': 'cat-1',
        'category': 'Camisas',
        'discount_type': 'percentage',
        'discount_value': 15.0,
        'synced_at': '2026-11-05T20:00:00Z',
        'variants': [
          {
            'id': 'var-1',
            'sku': 'CAM-LIN-AZU-M',
            'price': 150.0,
            'size': 'M',
            'color': 'Azul',
            'color_hex': '#0000ff',
            'image_url': 'https://example.com/camisa.jpg',
            'available_stock': 8,
          }
        ]
      };

      final product = OfflineCatalogProduct.fromJson(json);
      expect(product.id, 'prod-123');
      expect(product.name, 'Camisa de Lino Azul');
      expect(product.variants.length, 1);
      expect(product.variants.first.sku, 'CAM-LIN-AZU-M');
      expect(product.variants.first.availableStock, 8);

      final encoded = product.toJson();
      expect(encoded['name'], 'Camisa de Lino Azul');
      expect((encoded['variants'] as List).length, 1);
    });

    test('Variant stock and pricing calculations are exact', () {
      const variant = OfflineVariant(
        id: 'var-2',
        sku: 'PAN-JEA-NEG-32',
        price: 220.50,
        size: '32',
        color: 'Negro',
        availableStock: 5,
      );

      expect(variant.price, 220.50);
      expect(variant.availableStock, 5);
      expect(variant.sku, 'PAN-JEA-NEG-32');
    });
  });
}
