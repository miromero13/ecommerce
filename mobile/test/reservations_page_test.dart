import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/routes.dart';
import 'package:mobile/app/theme.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/catalog/catalog_api.dart';
import 'package:mobile/features/catalog/catalog_models.dart';
import 'package:mobile/features/reservations/reservation_api.dart';
import 'package:mobile/features/reservations/reservation_controller.dart';
import 'package:mobile/features/reservations/reservation_models.dart';
import 'package:mobile/features/reservations/reservation_create_page.dart';
import 'package:mobile/features/reservations/reservations_page.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('muestra solo la lista de reservas', (tester) async {
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
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Crear reserva'), findsNothing);
    expect(find.text('Aún no tienes reservas'), findsOneWidget);
    expect(reservationApi.createCalls, 0);
  });

  testWidgets('crea una reserva desde el flujo de preparación', (tester) async {
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
        home: ReservationCreatePage(
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
              ReservationDraftItem(
                variantId: 'variant-id-2',
                quantity: 2,
                productName: 'Pantalón demo',
                variantSku: 'SKU-2',
              ),
            ],
          ),
        ),
        onGenerateRoute: (settings) => MaterialPageRoute<void>(
          builder: (_) => const SizedBox.shrink(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Preparar reserva'), findsOneWidget);
    expect(find.text('Blusa demo'), findsOneWidget);
    expect(find.text('Pantalón demo'), findsOneWidget);
    await tester.tap(find.text('Selecciona una sucursal'));
    await tester.pump();
    await tester.tap(find.text('Sucursal Central · La Paz'));
    await tester.pump();
    await tester.tap(find.widgetWithText(FilledButton, 'Confirmar reserva'));
    await tester.pumpAndSettle();

    expect(reservationApi.createCalls, 1);
  });

  testWidgets('devuelve el borrador al catálogo para agregar otra prenda', (
    tester,
  ) async {
    final authController = AuthController(api: _FakeAuthApi());
    await authController.login(
      const LoginRequest(email: 'cliente@example.com', password: 'secret'),
    );
    final controller = ReservationController(
      api: _FakeReservationApi(),
      catalogApi: _FakeCatalogApi(),
    );
    addTearDown(() {
      authController.dispose();
      controller.dispose();
    });
    String? routeName;
    ReservationArguments? arguments;

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: ReservationCreatePage(
          authController: authController,
          controller: controller,
          arguments: const ReservationArguments(
            items: [
              ReservationDraftItem(
                variantId: 'variant-id',
                quantity: 1,
                productName: 'Blusa demo',
              ),
            ],
          ),
        ),
        onGenerateRoute: (settings) {
          routeName = settings.name;
          arguments = settings.arguments as ReservationArguments;
          return MaterialPageRoute<void>(
            builder: (_) => const SizedBox.shrink(),
          );
        },
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Agregar otra prenda'));
    await tester.pumpAndSettle();

    expect(routeName, AppRoutes.catalog);
    expect(arguments!.items.single.variantId, 'variant-id');
  });

  testWidgets('muestra un estado vacío sin formulario para un borrador vacío', (
    tester,
  ) async {
    final authController = AuthController(api: _FakeAuthApi());
    await authController.login(
      const LoginRequest(email: 'cliente@example.com', password: 'secret'),
    );
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
        home: ReservationCreatePage(
          authController: authController,
          controller: controller,
          arguments: const ReservationArguments(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Reserva sin prendas'), findsOneWidget);
    expect(find.text('Explorar catálogo'), findsOneWidget);
    expect(find.text('Sucursal para visitar'), findsNothing);
    expect(find.text('Confirmar reserva'), findsNothing);
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
