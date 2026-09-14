import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/catalog/catalog_api.dart';
import 'package:mobile/features/catalog/catalog_models.dart';
import 'package:mobile/features/reservations/reservation_api.dart';
import 'package:mobile/features/reservations/reservation_controller.dart';
import 'package:mobile/features/reservations/reservation_models.dart';
import 'package:mobile/features/reservations/reservations_page.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('crea y muestra una reserva autenticada', (tester) async {
    final authController = AuthController(api: _FakeAuthApi());
    await authController.login(
      const LoginRequest(email: 'cliente@example.com', password: 'secret'),
    );
    final reservationApi = _FakeReservationApi();
    final controller = ReservationController(
      api: reservationApi,
      catalogApi: _FakeCatalogApi(),
    );
    addTearDown(() {
      authController.dispose();
      controller.dispose();
    });

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(
          body: ReservationsPage(
            authController: authController,
            controller: controller,
            arguments: const ReservationArguments(
              items: [
                ReservationDraftItem(
                  variantId: 'variant-id',
                  quantity: 1,
                  productName: 'Blusa demo',
                  variantSku: 'SKU-1',
                ),
              ],
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Crear reserva'), findsNWidgets(2));
    expect(find.text('Sucursal Central · La Paz'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, 'Crear reserva'));
    await tester.pumpAndSettle();

    expect(reservationApi.createCalls, 1);
    expect(find.text('Reserva creada exitosamente'), findsOneWidget);
    expect(find.text('Sucursal Central'), findsOneWidget);
  });

  testWidgets('un invitado no carga reservas', (tester) async {
    final authController = AuthController(api: _FakeAuthApi());
    await authController.restoreSession();
    final controller = ReservationController(
      api: _FakeReservationApi(),
      catalogApi: _FakeCatalogApi(),
    );
    addTearDown(() {
      authController.dispose();
      controller.dispose();
    });

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(
          body: ReservationsPage(
            authController: authController,
            controller: controller,
          ),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('Reservas privadas'), findsOneWidget);
    expect(controller.reservations, isEmpty);
  });
}

class _FakeReservationApi extends ReservationApi {
  _FakeReservationApi() : super();

  var createCalls = 0;

  @override
  Future<ReservationListResult> getMine() async {
    return const ReservationListResult(
      reservations: [],
      message: 'Reservas obtenidas exitosamente',
    );
  }

  @override
  Future<ReservationResult> create({
    required String branchId,
    required DateTime visitDate,
    required List<ReservationDraftItem> items,
  }) async {
    createCalls++;
    return ReservationResult(
      reservation: _reservation,
      message: 'Reserva creada exitosamente',
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

class _FakeAuthApi extends AuthApi {
  _FakeAuthApi() : super();

  @override
  Future<AuthSession> login(LoginRequest request) async => _session;
}

final _reservation = Reservation(
  id: 'reservation-id',
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

const _session = AuthSession(
  accessToken: 'token',
  tokenType: 'bearer',
  user: User(
    id: 'user-id',
    name: 'Cliente Demo',
    email: 'cliente@example.com',
    gender: UserGender.femenino,
    rol: UserRole.cliente,
    branchId: null,
    isActive: true,
  ),
);
