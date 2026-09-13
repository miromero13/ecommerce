import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/cart/cart_api.dart';
import 'package:mobile/features/cart/cart_models.dart';
import 'package:mobile/features/catalog/catalog_models.dart';
import 'package:mobile/features/catalog/product_detail_page.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('un invitado puede cancelar login sin llamar al carrito', (
    tester,
  ) async {
    final authController = AuthController(api: _FakeAuthApi());
    await authController.restoreSession();
    final cartApi = _FakeCartApi();

    await tester.pumpWidget(_host(authController, cartApi));
    await _tapAddToCart(tester);
    expect(find.byTooltip('Cerrar'), findsOneWidget);

    await tester.tap(find.byTooltip('Cerrar'));
    await tester.pumpAndSettle();

    expect(cartApi.calls, 0);
    expect(authController.isAuthenticated, isFalse);
  });

  testWidgets(
    'reanuda la intención después de login y envía variante y cantidad',
    (tester) async {
      final authController = AuthController(
        api: _FakeAuthApi(session: _session),
      );
      await authController.restoreSession();
      final cartApi = _FakeCartApi();

      await tester.pumpWidget(_host(authController, cartApi));
      await _tapAddToCart(tester);

      await _fillLogin(tester);
      await tester.tap(find.widgetWithText(FilledButton, 'Iniciar sesión'));
      await tester.pumpAndSettle();

      expect(cartApi.calls, 1);
      expect(cartApi.variantId, 'variant-id');
      expect(cartApi.quantity, 2);
      expect(authController.isAuthenticated, isTrue);
      expect(find.text('Producto agregado al carrito'), findsOneWidget);
    },
  );
}

Future<void> _tapAddToCart(WidgetTester tester) async {
  await tester.drag(find.byType(ListView).first, const Offset(0, -900));
  await tester.pump(const Duration(milliseconds: 500));
  await tester.tap(find.byTooltip('Aumentar cantidad'));
  await tester.tap(find.widgetWithText(FilledButton, 'Agregar al carrito'));
  await tester.pump(const Duration(milliseconds: 500));
}

Future<void> _fillLogin(WidgetTester tester) async {
  final fields = find.byType(TextField);
  await tester.enterText(fields.at(0), 'cliente@example.com');
  await tester.enterText(fields.at(1), 'secret');
}

Widget _host(AuthController authController, CartApi cartApi) {
  return MaterialApp(
    theme: buildAppTheme(),
    home: ProductDetailPage(
      arguments: ProductDetailArguments(product: _product),
      authController: authController,
      cartApi: cartApi,
    ),
  );
}

class _FakeCartApi extends CartApi {
  var calls = 0;
  String? variantId;
  int? quantity;

  @override
  Future<CartOperationResult> addItem({
    required String variantId,
    required int quantity,
  }) async {
    calls++;
    this.variantId = variantId;
    this.quantity = quantity;
    return CartOperationResult(
      cart: _cart,
      message: 'Producto agregado al carrito',
    );
  }
}

final _cart = Cart(
  id: 'cart-id',
  userId: 'user-id',
  status: CartStatus.active,
  subtotal: 100,
  discountAmount: 0,
  totalAmount: 100,
  itemCount: 1,
  createdAt: DateTime.utc(2026, 1, 1),
  items: const [],
);

class _FakeAuthApi extends AuthApi {
  _FakeAuthApi({this.session});

  final AuthSession? session;

  @override
  Future<AuthSession> login(LoginRequest request) async => session!;

  @override
  Future<AuthSession> register(RegisterRequest request) async => session!;
}

const _product = Product(
  id: 'product-id',
  name: 'Producto demo',
  price: 100,
  categoryId: 'category-id',
  variants: [
    ProductVariant(
      id: 'variant-id',
      productId: 'product-id',
      sku: 'SKU-1',
      price: 100,
      status: ProductStatus.active,
    ),
  ],
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
