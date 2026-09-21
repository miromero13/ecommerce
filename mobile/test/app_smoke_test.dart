import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/app.dart';
import 'package:mobile/app/routes.dart';
import 'package:mobile/app/theme.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/auth/login_page.dart';
import 'package:mobile/features/catalog/catalog_controller.dart';
import 'package:mobile/shared/widgets/app_scaffold.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('valida sesión antes de mostrar la aplicación', (tester) async {
    final catalogController = _readyCatalogController();
    final authController = await _guestAuthController();
    addTearDown(catalogController.dispose);
    addTearDown(authController.dispose);
    await tester.pumpWidget(
      MobileApp(
        authController: authController,
        catalogController: catalogController,
      ),
    );

    await tester.pumpAndSettle();
    expect(find.byType(LoginPage), findsOneWidget);
    expect(find.text('Entrar como invitado'), findsOneWidget);
    await _enterAsGuest(tester);

    expect(find.text('Catálogo'), findsAtLeastNWidgets(1));
    expect(find.text('Catálogo público'), findsOneWidget);
    expect(find.byType(AppScaffold), findsOneWidget);
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.byType(NavigationDestination), findsNWidgets(3));

    final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
    expect(app.theme?.useMaterial3, isTrue);
    expect(app.theme?.colorScheme.primary, AppColors.coral);
    expect(app.theme?.scaffoldBackgroundColor, AppColors.white);
  });

  testWidgets('navega a superficies privadas sin bloquear el catálogo', (
    tester,
  ) async {
    final catalogController = _readyCatalogController();
    final authController = await _guestAuthController();
    addTearDown(catalogController.dispose);
    addTearDown(authController.dispose);
    await tester.pumpWidget(
      MobileApp(
        authController: authController,
        catalogController: catalogController,
      ),
    );

    await _enterAsGuest(tester);
    await tester.tap(find.text('Gestiones'));
    await tester.pumpAndSettle();

    expect(find.text('Mis reservas'), findsOneWidget);
    expect(find.text('Mis pedidos'), findsOneWidget);
    await tester.tap(find.text('Mis reservas'));
    await tester.pumpAndSettle();
    expect(
      find.text('Inicia sesión para consultar tus reservas.'),
      findsOneWidget,
    );
    expect(find.byType(AppScaffold), findsOneWidget);

    await tester.tap(
      find.descendant(
        of: find.byType(NavigationBar),
        matching: find.text('Catálogo'),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Catálogo público'), findsOneWidget);

    await tester.tap(find.text('Carrito'));
    await tester.pumpAndSettle();
    expect(find.text('Carrito privado'), findsOneWidget);
    expect(find.text('Carrito'), findsAtLeastNWidgets(1));
  });

  testWidgets('mantiene detalle y login como rutas públicas', (tester) async {
    final catalogController = _readyCatalogController();
    final authController = await _guestAuthController();
    addTearDown(catalogController.dispose);
    addTearDown(authController.dispose);
    await tester.pumpWidget(
      MobileApp(
        authController: authController,
        catalogController: catalogController,
      ),
    );

    await _enterAsGuest(tester);
    final navigator = tester.state<NavigatorState>(find.byType(Navigator));
    navigator.pushNamed(AppRoutes.productDetail);
    await tester.pumpAndSettle();
    expect(
      find.text('El detalle reutilizará el producto del catálogo.'),
      findsOneWidget,
    );
    expect(find.byType(NavigationBar), findsNothing);

    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Carrito'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Iniciar sesión'));
    await tester.pumpAndSettle();
    expect(find.byType(LoginPage), findsOneWidget);
    expect(find.text('Correo electrónico'), findsOneWidget);
  });
}

CatalogController _readyCatalogController() {
  final controller = CatalogController();
  controller.status = CatalogStatus.ready;
  return controller;
}

Future<AuthController> _guestAuthController() async {
  final controller = AuthController();
  await controller.restoreSession();
  return controller;
}

Future<void> _enterAsGuest(WidgetTester tester) async {
  await tester.pumpAndSettle();
  await tester.tap(find.text('Entrar como invitado'));
  await tester.pumpAndSettle();
}
