import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/deliveries/delivery_models.dart';
import 'package:mobile/features/rma/rma_models.dart';

void main() {
  group('DeliveryOrder parsing', () {
    test('parsea correctamente orden de delivery activa con PIN', () {
      final json = {
        'order_id': 'ord-123',
        'tenant_name': 'Ayni Moda',
        'branch_name': 'Sucursal Central',
        'branch_city': 'Santa Cruz',
        'client_name': 'María Quispe',
        'address': 'Av. San Martín 450',
        'reference': 'Puerta blanca',
        'distance_km': 4.2,
        'shipping_cost': 15.0,
        'total_amount': 250.0,
        'currency': 'BOB',
        'status': 'in_transit',
        'driver_name': 'Javier Mamani',
        'created_at': '2026-11-05T12:00:00Z',
        'delivery_pin': '8492',
      };

      final delivery = DeliveryOrder.fromJson(json);

      expect(delivery.orderId, 'ord-123');
      expect(delivery.tenantName, 'Ayni Moda');
      expect(delivery.address, 'Av. San Martín 450');
      expect(delivery.shippingCost, 15.0);
      expect(delivery.totalAmount, 250.0);
      expect(delivery.status, 'in_transit');
      expect(delivery.driverName, 'Javier Mamani');
      expect(delivery.deliveryPin, '8492');
      expect(delivery.isActive, isTrue);
      expect(delivery.statusLabel, 'En camino');
    });

    test('reconoce estado delivered como no activo', () {
      final json = {
        'order_id': 'ord-456',
        'tenant_name': 'Ayni Moda',
        'address': 'Calle 2',
        'shipping_cost': 10.0,
        'total_amount': 100.0,
        'currency': 'BOB',
        'status': 'delivered',
        'created_at': '2026-11-05T10:00:00Z',
        'delivered_at': '2026-11-05T11:00:00Z',
      };

      final delivery = DeliveryOrder.fromJson(json);
      expect(delivery.isActive, isFalse);
      expect(delivery.statusLabel, 'Entregado');
      expect(delivery.deliveredAt, isNotNull);
    });
  });

  group('RMA models parsing', () {
    test('parsea EligibleOrder e ítems con variantes para cambio', () {
      final json = {
        'order_id': 'ord-789',
        'order_number': 'ORD-789',
        'created_at': '2026-11-01T10:00:00Z',
        'days_since_delivery': 4,
        'items': [
          {
            'order_item_id': 'item-1',
            'product_id': 'prod-1',
            'product_name': 'Camisa Oxford',
            'variant_id': 'var-1',
            'sku': 'OXF-M-BLU',
            'size_name': 'M',
            'color_name': 'Azul',
            'unit_price': 180.0,
            'quantity': 1,
            'eligible_for_rma': true,
            'same_product_variants': [
              {
                'variant_id': 'var-2',
                'sku': 'OXF-L-BLU',
                'size_name': 'L',
                'color_name': 'Azul',
                'stock': 5,
              },
            ],
          },
        ],
      };

      final order = EligibleOrder.fromJson(json);
      expect(order.orderId, 'ord-789');
      expect(order.orderNumber, 'ORD-789');
      expect(order.daysSinceDelivery, 4);
      expect(order.items.length, 1);

      final item = order.items.first;
      expect(item.productName, 'Camisa Oxford');
      expect(item.sizeName, 'M');
      expect(item.eligibleForRma, isTrue);
      expect(item.sameProductVariants.length, 1);
      expect(item.sameProductVariants.first.label, contains('L · Azul'));
    });

    test('parsea RmaRequest y RmaItem con acta de merma y resolución', () {
      final json = {
        'id': 'rma-001',
        'rma_number': 'RMA-2026-0001',
        'order_id': 'ord-789',
        'order_number': 'ORD-789',
        'status': 'pending_inspection',
        'customer_notes': 'Queda chica la talla',
        'pdf_url': '/api/rma/requests/rma-001/pdf',
        'created_at': '2026-11-05T14:00:00Z',
        'items': [
          {
            'id': 'rma-item-1',
            'product_name': 'Camisa Oxford',
            'original_sku': 'OXF-M-BLU',
            'original_size': 'M',
            'unit_price': 180.0,
            'quantity': 1,
            'reason': 'size_change',
            'preferred_resolution': 'exchange',
            'requested_variant_label': 'L · Azul',
            'status': 'pending_inspection',
          },
          {
            'id': 'rma-item-2',
            'product_name': 'Pantalón Chino',
            'original_sku': 'CHI-32-BEI',
            'unit_price': 220.0,
            'quantity': 1,
            'reason': 'factory_defect',
            'preferred_resolution': 'store_credit',
            'status': 'accepted_scrap',
            'quarantine_record': 'QR-2026-0044',
            'refund_amount': 220.0,
          },
        ],
      };

      final rma = RmaRequest.fromJson(json);
      expect(rma.rmaNumber, 'RMA-2026-0001');
      expect(rma.statusLabel, 'Pendiente en sucursal');
      expect(rma.items.length, 2);

      final item1 = rma.items[0];
      expect(item1.reasonLabel, 'Cambio de talla');
      expect(item1.resolutionLabel, 'Cambio por otra prenda');

      final item2 = rma.items[1];
      expect(item2.reasonLabel, 'Falla / Defecto de fábrica');
      expect(item2.resolutionLabel, 'Saldo en Billetera Digital');
      expect(item2.quarantineRecord, 'QR-2026-0044');
      expect(item2.refundAmount, 220.0);
    });
  });
}
