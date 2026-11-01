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
      'tenant_id': 'tenant-uuid',
      'tenant_name': 'Ayni Moda',
      'branch_id': 'branch-uuid',
      'branch_name': 'Sucursal Central',
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
    expect(cart.tenantId, 'tenant-uuid');
    expect(cart.tenantName, 'Ayni Moda');
    expect(cart.branchId, 'branch-uuid');
    expect(cart.branchName, 'Sucursal Central');
    expect(cart.items.single.imageUrl, 'https://example.com/image.jpg');
    expect(cart.items.single.colorName, 'Negro');
  });

  test('carrito bloqueado por pedido pendiente de pago', () {
    Map<String, dynamic> json(Map<String, dynamic> extra) => {
      'id': 'cart-id',
      'user_id': 'user-id',
      'status': 'active',
      'subtotal': 10,
      'discount_amount': 0,
      'total_amount': 10,
      'item_count': 1,
      'created_at': '2026-01-01T10:00:00Z',
      'items': [],
      ...extra,
    };

    final free = Cart.fromJson(json({}));
    expect(free.isLocked, isFalse);
    expect(free.pendingOrderId, isNull);
    expect(free.pendingOrderExpiresAt, isNull);

    final locked = Cart.fromJson(json({
      'status': 'checkout_pending',
      'pending_order_id': 'order-id',
      'pending_order_expires_at': '2026-01-01T10:40:00Z',
    }));
    expect(locked.isLocked, isTrue);
    expect(locked.pendingOrderId, 'order-id');
    expect(locked.pendingOrderExpiresAt, DateTime.utc(2026, 1, 1, 10, 40));
  });

  test('rechaza un estado de carrito desconocido', () {
    expect(
      () => CartStatus.fromJson('unknown'),
      throwsA(isA<FormatException>()),
    );
  });
}
