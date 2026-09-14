import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/catalog/catalog_api.dart';
import 'package:mobile/features/catalog/catalog_models.dart';
import 'package:mobile/features/reservations/reservation_api.dart';
import 'package:mobile/features/reservations/reservation_controller.dart';
import 'package:mobile/features/reservations/reservation_models.dart';

void main() {
  test('carga, crea y cancela reservas', () async {
    final api = _FakeReservationApi();
    final controller = ReservationController(
      api: api,
      catalogApi: _FakeCatalogApi(),
    );

    await controller.load();
    expect(controller.status, ReservationControllerStatus.ready);
    expect(controller.reservations, hasLength(1));
    expect(controller.branches, hasLength(1));

    await controller.create(
      branchId: 'branch-id',
      visitDate: DateTime(2026, 9, 10),
      items: const [ReservationDraftItem(variantId: 'variant-id', quantity: 1)],
    );
    expect(controller.reservations, hasLength(2));

    await controller.cancel('reservation-id');
    expect(
      controller.reservations
          .where((reservation) => reservation.id == 'reservation-id')
          .single
          .status,
      ReservationStatus.cancelled,
    );

    await controller.loadDetail('reservation-id');
    expect(controller.selectedReservation?.id, 'reservation-id');
  });
}

class _FakeReservationApi extends ReservationApi {
  _FakeReservationApi() : super();

  @override
  Future<ReservationListResult> getMine() async {
    return ReservationListResult(
      reservations: [_reservation(ReservationStatus.pending)],
      message: 'Reservas obtenidas exitosamente',
    );
  }

  @override
  Future<ReservationResult> create({
    required String branchId,
    required DateTime visitDate,
    required List<ReservationDraftItem> items,
  }) async {
    return ReservationResult(
      reservation: _createdReservation,
      message: 'Reserva creada exitosamente',
    );
  }

  @override
  Future<ReservationResult> cancel({required String reservationId}) async {
    return ReservationResult(
      reservation: _reservation(ReservationStatus.cancelled),
      message: 'Reserva cancelada exitosamente',
    );
  }

  @override
  Future<ReservationResult> getById({required String reservationId}) async {
    return ReservationResult(
      reservation: _reservation(ReservationStatus.cancelled),
      message: 'Reserva obtenida exitosamente',
    );
  }
}

class _FakeCatalogApi extends CatalogApi {
  _FakeCatalogApi() : super();

  @override
  Future<List<Branch>> getBranches() async => const [
    Branch(
      id: 'branch-id',
      name: 'Sucursal Central',
      city: 'La Paz',
      isDefault: true,
      isActive: true,
    ),
  ];
}

Reservation _reservation(ReservationStatus status) {
  return Reservation(
    id: 'reservation-id',
    branchId: 'branch-id',
    branchName: 'Sucursal Central',
    userId: 'user-id',
    visitDate: DateTime(2026, 9, 10),
    expiresAt: DateTime(2026, 9, 11),
    status: status,
    totalAmount: 100,
    itemCount: 1,
    createdAt: DateTime.utc(2026, 9, 1),
    items: const [],
  );
}

final _createdReservation = Reservation(
  id: 'created-id',
  branchId: 'branch-id',
  branchName: 'Sucursal Central',
  userId: 'user-id',
  visitDate: DateTime(2026, 9, 10),
  expiresAt: DateTime(2026, 9, 11),
  status: ReservationStatus.pending,
  totalAmount: 100,
  itemCount: 1,
  createdAt: DateTime.utc(2026, 9, 1),
  items: const [],
);
