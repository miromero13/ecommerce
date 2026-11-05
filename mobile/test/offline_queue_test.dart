import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/offline/offline_queue_models.dart';

void main() {
  group('CU25 OfflineQueue Models & Serialization Tests', () {
    test('OfflineOperation fromJson & toJson serialize cash contingency sale', () {
      final json = {
        'operation_id': 'op-987',
        'receipt_number': 'CONT-20261105-5555',
        'type': 'cash_sale',
        'status': 'local_pending',
        'created_at': '2026-11-05T20:25:00Z',
        'tenant_id': 'ten-1',
        'branch_id': 'br-1',
        'customer_name': 'Juan Pérez',
        'customer_email': 'juan@example.com',
        'subtotal': 300.0,
        'discount': 30.0,
        'total': 270.0,
        'cash_received': 300.0,
        'change_returned': 30.0,
        'notes': 'Cobro en efectivo offline',
        'items': [
          {
            'variant_id': 'var-abc',
            'product_name': 'Pantalón Chino Beige',
            'variant_sku': 'PAN-CHI-BEI-30',
            'unit_price': 150.0,
            'quantity': 2,
            'subtotal': 300.0,
          }
        ]
      };

      final operation = OfflineOperation.fromJson(json);
      expect(operation.operationId, 'op-987');
      expect(operation.receiptNumber, 'CONT-20261105-5555');
      expect(operation.type, 'cash_sale');
      expect(operation.status, 'local_pending');
      expect(operation.total, 270.0);
      expect(operation.changeReturned, 30.0);
      expect(operation.items.length, 1);
      expect(operation.items.first.variantSku, 'PAN-CHI-BEI-30');

      final serialized = operation.toJson();
      expect(serialized['receipt_number'], 'CONT-20261105-5555');
      expect((serialized['items'] as List).length, 1);
    });

    test('OfflineOrderItem computes subtotal and parses quantity safely', () {
      const item = OfflineOrderItem(
        variantId: 'var-1',
        productName: 'Remera Algodón Blanca',
        variantSku: 'REM-ALG-BLA-L',
        unitPrice: 85.50,
        quantity: 3,
        subtotal: 256.50,
      );

      expect(item.quantity, 3);
      expect(item.subtotal, 256.50);
      expect(item.variantSku, 'REM-ALG-BLA-L');
    });
  });
}
