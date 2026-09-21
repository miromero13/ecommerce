import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/profile/profile_api.dart';
import 'package:mobile/features/profile/profile_controller.dart';
import 'package:mobile/features/profile/profile_page.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('consulta, edita y sincroniza el perfil autenticado', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(280, 640));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    final authController = AuthController(api: _FakeAuthApi());
    await authController.login(
      const LoginRequest(email: 'cliente@example.com', password: 'secret'),
    );
    final profileApi = _FakeProfileApi();
    final profileController = ProfileController(
      api: profileApi,
      authController: authController,
    );
    addTearDown(() {
      authController.dispose();
      profileController.dispose();
    });

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(
          body: ProfilePage(
            authController: authController,
            controller: profileController,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Cliente Demo'), findsOneWidget);
    expect(find.text('cliente@example.com'), findsOneWidget);
    expect(find.text('Mis reservas'), findsOneWidget);

    await tester.tap(find.text('Editar perfil'));
    await tester.pump();
    expect(tester.takeException(), isNull);
    await tester.enterText(find.byType(TextField).at(0), 'Cliente Actualizado');
    await tester.enterText(
      find.byType(TextField).at(1),
      'actualizado@example.com',
    );
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();

    expect(profileApi.updatedName, 'Cliente Actualizado');
    expect(authController.user?.name, 'Cliente Actualizado');
    expect(find.text('Cliente Actualizado'), findsOneWidget);
    expect(find.text('Perfil actualizado exitosamente'), findsOneWidget);

    await tester.drag(find.byType(ListView).first, const Offset(0, -500));
    await tester.pump();
    await tester.tap(find.text('Cerrar sesión'));
    await tester.pumpAndSettle();
    expect(find.text('Cuenta privada'), findsOneWidget);
  });

  testWidgets('un invitado no consulta ni crea perfil local', (tester) async {
    final authController = AuthController(api: _FakeAuthApi());
    await authController.restoreSession();
    final profileApi = _FakeProfileApi();
    final profileController = ProfileController(api: profileApi);
    addTearDown(() {
      authController.dispose();
      profileController.dispose();
    });

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(
          body: ProfilePage(
            authController: authController,
            controller: profileController,
          ),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('Cuenta privada'), findsOneWidget);
    expect(profileApi.getCalls, 0);
    expect(profileController.profile, isNull);
  });
}

class _FakeProfileApi extends ProfileApi {
  _FakeProfileApi() : super();

  var getCalls = 0;
  String? updatedName;

  @override
  Future<ProfileOperationResult> getProfile() async {
    getCalls++;
    return ProfileOperationResult(
      user: _user,
      message: 'Perfil obtenido correctamente',
    );
  }

  @override
  Future<ProfileOperationResult> updateProfile({
    required String name,
    required String email,
    required UserGender gender,
  }) async {
    updatedName = name;
    return ProfileOperationResult(
      user: User(
        id: _user.id,
        name: name,
        email: email,
        gender: gender,
        rol: _user.rol,
        branchId: _user.branchId,
        isActive: _user.isActive,
      ),
      message: 'Perfil actualizado exitosamente',
    );
  }
}

class _FakeAuthApi extends AuthApi {
  _FakeAuthApi() : super();

  @override
  Future<AuthSession> login(LoginRequest request) async => _session;
}

const _user = User(
  id: 'user-id',
  name: 'Cliente Demo',
  email: 'cliente@example.com',
  gender: UserGender.femenino,
  rol: UserRole.cliente,
  branchId: null,
  isActive: true,
);

const _session = AuthSession(
  accessToken: 'token',
  tokenType: 'bearer',
  user: _user,
);
