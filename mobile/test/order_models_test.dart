import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/orders/order_models.dart';

void main() {
  test('parsea pedido, estados, moneda, totales e ítems', () {
    final order = Order.fromJson({
      'id': 'order-id',
      'user_id': 'user-id',
      'status': 'paid',
      'payment_method': 'cash',
      'payment_status': 'paid',
      'stripe_payment_intent_id': null,
      'cash_reference': 'CASH-001',
      'subtotal': '125.50',
      'discount_amount': '5.50',
      'total_amount': '120.00',
      'currency': 'usd',
      'created_at': '2026-09-01T10:00:00Z',
      'updated_at': null,
      'items': [
        {
          'id': 'item-id',
          'order_id': 'order-id',
          'variant_id': 'variant-id',
          'quantity': 2,
          'unit_price': '60.00',
          'line_total': '120.00',
          'product_id': 'product-id',
          'product_name': 'Blusa demo',
          'variant_sku': 'SKU-1',
          'size_id': null,
          'color_id': null,
          'size_name': 'M',
          'color_name': 'Negro',
          'image_url': null,
          'image_public_id': 'ignored',
        },
      ],
    });

    expect(order.status, OrderStatus.paid);
    expect(order.paymentMethod, PaymentMethod.cash);
    expect(order.paymentStatus, PaymentStatus.paid);
    expect(order.totalAmount, 120);
    expect(order.items.single.productName, 'Blusa demo');
    expect(order.items.single.sizeName, 'M');
  });

  test('rechaza estados desconocidos', () {
    expect(() => OrderStatus.fromJson('unknown'), throwsFormatException);
  });
}
