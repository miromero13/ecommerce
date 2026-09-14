import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/cart/cart_api.dart';
import 'package:mobile/features/cart/cart_controller.dart';
import 'package:mobile/features/cart/cart_models.dart';
import 'package:mobile/features/cart/cart_page.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('muestra el carrito autenticado y actualiza cantidades', (
    tester,
  ) async {
    final authController = AuthController(api: _FakeAuthApi());
    await authController.login(
      const LoginRequest(email: 'cliente@example.com', password: 'secret'),
    );
    final cartApi = _FakeCartApi();
    final cartController = CartController(api: cartApi);
    addTearDown(() {
      authController.dispose();
      cartController.dispose();
    });

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(
          body: CartPage(
            authController: authController,
            controller: cartController,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Blusa demo'), findsOneWidget);
    expect(find.text('Bs 125.50'), findsNWidgets(2));
    expect(find.text('Bs 120.50'), findsOneWidget);

    await tester.tap(find.byTooltip('Aumentar cantidad'));
    await tester.pumpAndSettle();

    expect(cartApi.updatedItemId, 'item-id');
    expect(cartApi.updatedQuantity, 2);
    expect(find.text('2'), findsOneWidget);
  });

  testWidgets('un invitado no carga un carrito local', (tester) async {
    final authController = AuthController(api: _FakeAuthApi());
    await authController.restoreSession();
    final cartController = CartController(api: _FakeCartApi());
    addTearDown(() {
      authController.dispose();
      cartController.dispose();
    });

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(
          body: CartPage(
            authController: authController,
            controller: cartController,
          ),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('Carrito privado'), findsOneWidget);
    expect(cartController.cart, isNull);
  });
}

class _FakeCartApi extends CartApi {
  _FakeCartApi() : super();

  String? updatedItemId;
  int? updatedQuantity;

  @override
  Future<CartOperationResult> getCurrent() async {
    return _result('Carrito obtenido exitosamente', 1);
  }

  @override
  Future<CartOperationResult> updateItem({
    required String itemId,
    required int quantity,
  }) async {
    updatedItemId = itemId;
    updatedQuantity = quantity;
    return _result('Carrito actualizado exitosamente', quantity);
  }

  CartOperationResult _result(String message, int quantity) {
    return CartOperationResult(cart: _cart(quantity), message: message);
  }
}

class _FakeAuthApi extends AuthApi {
  _FakeAuthApi() : super();

  @override
  Future<AuthSession> login(LoginRequest request) async => _session;
}

Cart _cart(int quantity) {
  return Cart(
    id: 'cart-id',
    userId: 'user-id',
    status: CartStatus.active,
    subtotal: 125.50 * quantity,
    discountAmount: 5,
    totalAmount: 120.50 * quantity,
    itemCount: quantity,
    createdAt: DateTime.utc(2026, 1, 1),
    items: [
      CartItem(
        id: 'item-id',
        cartId: 'cart-id',
        variantId: 'variant-id',
        quantity: quantity,
        unitPrice: 125.50,
        lineTotal: 125.50 * quantity,
        productId: 'product-id',
        productName: 'Blusa demo',
        variantSku: 'SKU-1',
        sizeName: 'M',
        colorName: 'Negro',
        imageUrl: null,
      ),
    ],
  );
}

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
