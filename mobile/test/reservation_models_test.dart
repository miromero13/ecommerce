import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/reservations/reservation_models.dart';

void main() {
  test('parsea reserva, estados, fechas, totales e ítems', () {
    final reservation = Reservation.fromJson({
      'id': 'reservation-id',
      'branch_id': 'branch-id',
      'branch_name': 'Sucursal Central',
      'user_id': 'user-id',
      'visit_date': '2026-09-10',
      'expires_at': '2026-09-11',
      'status': 'pending',
      'total_amount': '125.50',
      'item_count': 2,
      'created_at': '2026-09-01T10:00:00Z',
      'updated_at': null,
      'items': [
        {
          'id': 'item-id',
          'reservation_id': 'reservation-id',
          'variant_id': 'variant-id',
          'quantity': 2,
          'unit_price': '62.75',
          'line_total': '125.50',
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

    expect(reservation.status, ReservationStatus.pending);
    expect(reservation.canCancel, isTrue);
    expect(reservation.visitDate, DateTime(2026, 9, 10));
    expect(reservation.totalAmount, 125.5);
    expect(reservation.items.single.productName, 'Blusa demo');
  });

  test('serializa la fecha de creación sin hora', () {
    expect(formatReservationDate(DateTime(2026, 9, 10, 15, 30)), '2026-09-10');
  });
}
