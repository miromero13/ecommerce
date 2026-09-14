import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/auth/login_dialog.dart';
import 'package:mobile/features/auth/login_page.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('muestra el error del backend y conserva el diálogo', (
    tester,
  ) async {
    final controller = AuthController(
      api: _FakeAuthApi(
        failure: const ApiException(
          statusCode: 401,
          message: 'Credenciales incorrectas',
        ),
      ),
    );

    await tester.pumpWidget(_host(controller));
    await tester.tap(find.text('Abrir login'));
    await tester.pumpAndSettle();
    await _fillLogin(tester);
    await tester.tap(find.widgetWithText(FilledButton, 'Iniciar sesión'));
    await tester.pumpAndSettle();

    expect(find.text('Credenciales incorrectas'), findsOneWidget);
    expect(find.byType(LoginPage), findsOneWidget);
  });

  testWidgets('cierra el diálogo después de un login exitoso', (tester) async {
    final controller = AuthController(api: _FakeAuthApi(session: _session));

    await tester.pumpWidget(_host(controller));
    await tester.tap(find.text('Abrir login'));
    await tester.pumpAndSettle();
    await _fillLogin(tester);
    await tester.tap(find.widgetWithText(FilledButton, 'Iniciar sesión'));
    await tester.pumpAndSettle();

    expect(find.byType(LoginPage), findsNothing);
    expect(controller.isAuthenticated, isTrue);
  });

  testWidgets('permite cambiar a registro desde el diálogo', (tester) async {
    final controller = AuthController(api: _FakeAuthApi(session: _session));

    await tester.pumpWidget(_host(controller));
    await tester.tap(find.text('Abrir login'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Crear una cuenta'));
    await tester.pumpAndSettle();

    expect(find.text('Nombre'), findsOneWidget);
    expect(find.text('Género'), findsOneWidget);
    expect(find.text('Iniciar sesión'), findsNothing);
    expect(find.text('Crear cuenta'), findsAtLeastNWidgets(1));
  });
}

Future<void> _fillLogin(WidgetTester tester) async {
  final fields = find.byType(TextField);
  await tester.enterText(fields.at(0), 'cliente@example.com');
  await tester.enterText(fields.at(1), 'secret');
}

Widget _host(AuthController controller) {
  return MaterialApp(
    theme: buildAppTheme(),
    home: Scaffold(
      body: Builder(
        builder: (context) => TextButton(
          onPressed: () =>
              LoginDialog.show(context: context, controller: controller),
          child: const Text('Abrir login'),
        ),
      ),
    ),
  );
}

class _FakeAuthApi extends AuthApi {
  _FakeAuthApi({this.session, this.failure}) : super();

  final AuthSession? session;
  final Object? failure;

  @override
  Future<AuthSession> login(LoginRequest request) async {
    if (failure != null) throw failure!;
    return session!;
  }

  @override
  Future<AuthSession> register(RegisterRequest request) async {
    if (failure != null) throw failure!;
    return session!;
  }
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
