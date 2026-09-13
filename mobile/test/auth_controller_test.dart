import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/core/storage/session_storage.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/auth/auth_models.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  test('inicia como invitado cuando no existe token', () async {
    final controller = AuthController(api: _FakeAuthApi());

    await controller.restoreSession();

    expect(controller.status, AuthStatus.guest);
    expect(controller.isAuthenticated, isFalse);
    expect(controller.hasGuestAccess, isFalse);
  });

  test('habilita el acceso público al continuar como invitado', () {
    final controller = AuthController(api: _FakeAuthApi());

    controller.continueAsGuest();

    expect(controller.status, AuthStatus.guest);
    expect(controller.hasGuestAccess, isTrue);
  });

  test('restaura y valida una sesión con users/me', () async {
    const storage = SessionStorage();
    await storage.saveSession(
      accessToken: 'stored-token',
      user: _userJson,
      role: 'cliente',
    );
    final api = _FakeAuthApi(user: _user);
    final controller = AuthController(api: api, storage: storage);

    await controller.restoreSession();

    expect(api.currentUserCalls, 1);
    expect(controller.status, AuthStatus.authenticated);
    expect(controller.user, _user);
  });

  test('limpia una sesión cuando users/me responde 401', () async {
    const storage = SessionStorage();
    await storage.saveSession(
      accessToken: 'expired-token',
      user: _userJson,
      role: 'cliente',
    );
    final controller = AuthController(
      api: _FakeAuthApi(
        failure: const ApiException(statusCode: 401, message: 'Token inválido'),
      ),
      storage: storage,
    );

    await controller.restoreSession();

    expect(controller.status, AuthStatus.guest);
    expect(await storage.readAccessToken(), isNull);
    expect(await storage.readUser(), isNull);
  });

  test('expone error sin autenticar un token no validado', () async {
    const storage = SessionStorage();
    await storage.saveSession(
      accessToken: 'unreachable-token',
      user: _userJson,
      role: 'cliente',
    );
    final controller = AuthController(
      api: _FakeAuthApi(
        failure: const ApiException(
          statusCode: 503,
          message: 'Servidor no disponible',
        ),
      ),
      storage: storage,
    );

    await controller.restoreSession();

    expect(controller.status, AuthStatus.error);
    expect(controller.isAuthenticated, isFalse);
    expect(controller.errorMessage, 'Servidor no disponible');
  });

  test('guarda login, registro y cierre de sesión', () async {
    const storage = SessionStorage();
    final controller = AuthController(
      api: _FakeAuthApi(session: _session),
      storage: storage,
    );

    expect(
      await controller.login(
        const LoginRequest(email: 'cliente@example.com', password: 'secret'),
      ),
      isTrue,
    );
    expect(controller.status, AuthStatus.authenticated);
    expect(await storage.readAccessToken(), 'token');

    expect(
      await controller.register(
        const RegisterRequest(
          name: 'Cliente',
          email: 'cliente@example.com',
          password: 'secret',
          gender: UserGender.femenino,
        ),
      ),
      isTrue,
    );

    await controller.logout();
    expect(controller.status, AuthStatus.guest);
    expect(await storage.readAccessToken(), isNull);
  });
}

class _FakeAuthApi extends AuthApi {
  _FakeAuthApi({this.user, this.session, this.failure}) : super();

  final User? user;
  final AuthSession? session;
  final Object? failure;
  var currentUserCalls = 0;

  @override
  Future<User> currentUser() async {
    currentUserCalls++;
    if (failure != null) throw failure!;
    return user!;
  }

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

const _user = User(
  id: 'user-id',
  name: 'Cliente Demo',
  email: 'cliente@example.com',
  gender: UserGender.femenino,
  rol: UserRole.cliente,
  branchId: null,
  isActive: true,
);

const _userJson = {
  'id': 'user-id',
  'name': 'Cliente Demo',
  'email': 'cliente@example.com',
  'gender': 'femenino',
  'rol': 'cliente',
  'branch_id': null,
  'is_active': true,
};

const _session = AuthSession(
  accessToken: 'token',
  tokenType: 'bearer',
  user: _user,
);
