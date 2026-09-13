import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/cart/cart_models.dart';

void main() {
  test('parsea carrito, precios, cantidades e ítems', () {
    final cart = Cart.fromJson({
      'id': 'cart-id',
      'user_id': 'user-id',
      'status': 'active',
      'subtotal': '125.50',
      'discount_amount': 5,
      'total_amount': 120.5,
      'item_count': 2,
      'created_at': '2026-01-01T10:00:00Z',
      'updated_at': null,
      'items': [
        {
          'id': 'item-id',
          'cart_id': 'cart-id',
          'variant_id': 'variant-id',
          'quantity': 2,
          'unit_price': '62.75',
          'line_total': '125.50',
          'product_id': 'product-id',
          'product_name': 'Blusa demo',
          'variant_sku': 'SKU-1',
          'size_id': null,
          'color_id': 'color-id',
          'size_name': null,
          'color_name': 'Negro',
          'image_url': 'https://example.com/image.jpg',
          'image_public_id': 'ignored',
        },
      ],
    });

    expect(cart.status, CartStatus.active);
    expect(cart.subtotal, 125.5);
    expect(cart.discountAmount, 5);
    expect(cart.totalAmount, 120.5);
    expect(cart.itemCount, 2);
    expect(cart.items.single.imageUrl, 'https://example.com/image.jpg');
    expect(cart.items.single.colorName, 'Negro');
  });

  test('rechaza un estado de carrito desconocido', () {
    expect(
      () => CartStatus.fromJson('unknown'),
      throwsA(isA<FormatException>()),
    );
  });
}
