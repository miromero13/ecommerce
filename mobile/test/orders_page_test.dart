import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/orders/order_api.dart';
import 'package:mobile/features/orders/order_controller.dart';
import 'package:mobile/features/orders/order_models.dart';
import 'package:mobile/features/orders/orders_page.dart';

void main() {
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  testWidgets('carga pedidos y muestra el detalle con pago pendiente', (
    tester,
  ) async {
    final authController = AuthController(api: _FakeAuthApi());
    await authController.login(
      const LoginRequest(email: 'cliente@example.com', password: 'secret'),
    );
    final controller = OrderController(api: _FakeOrderApi());
    addTearDown(() {
      authController.dispose();
      controller.dispose();
    });

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(
          body: OrdersPage(
            authController: authController,
            controller: controller,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Mis pedidos'), findsOneWidget);
    await tester.tap(find.textContaining('Pedido order-12'));
    await tester.pumpAndSettle();

    expect(find.text('Pago: Pendiente'), findsOneWidget);
    expect(find.text('Pedido: Pendiente'), findsOneWidget);
    expect(find.text('Bs 120.00'), findsOneWidget);
  });
}

class _FakeAuthApi extends AuthApi {
  _FakeAuthApi() : super();

  @override
  Future<AuthSession> login(LoginRequest request) async => _session;
}

class _FakeOrderApi extends OrderApi {
  _FakeOrderApi() : super();

  @override
  Future<OrderListResult> getMine() async => const OrderListResult(
    orders: [_order],
    message: 'Pedidos obtenidos exitosamente',
  );

  @override
  Future<List<PickupBranch>> getPublicBranches() async => const [];

  @override
  Future<OrderResult> getById({required String orderId}) async => const OrderResult(
    order: _order,
    message: 'Pedido obtenido exitosamente',
  );
}

const _order = Order(
  id: 'order-12345678',
  userId: 'user-id',
  status: OrderStatus.pending,
  paymentMethod: PaymentMethod.cash,
  paymentStatus: PaymentStatus.pending,
  subtotal: 120,
  discountAmount: 0,
  totalAmount: 120,
  currency: 'BOB',
  createdAt: DateTime(2026, 9, 20),
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
