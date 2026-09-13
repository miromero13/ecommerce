import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/auth/auth_models.dart';

void main() {
  test('construye el payload real de login con rol cliente', () {
    const request = LoginRequest(
      email: ' cliente@example.com ',
      password: 'secret',
    );

    expect(request.toJson(), {
      'email': 'cliente@example.com',
      'password': 'secret',
      'rol': 'cliente',
    });
  });

  test('construye el payload real de registro sin enviar rol', () {
    const request = RegisterRequest(
      name: 'Cliente Demo',
      email: ' cliente@example.com ',
      password: 'secret',
      gender: UserGender.femenino,
    );

    expect(request.toJson(), {
      'name': 'Cliente Demo',
      'email': 'cliente@example.com',
      'password': 'secret',
      'gender': 'femenino',
    });
  });

  test('parsea la sesión y el usuario del backend', () {
    final session = AuthSession.fromJson({
      'access_token': 'token',
      'token_type': 'bearer',
      'user': {
        'id': 'user-id',
        'name': 'Cliente Demo',
        'email': 'cliente@example.com',
        'gender': 'masculino',
        'rol': 'cliente',
        'branch_id': null,
        'is_active': true,
      },
    });

    expect(session.accessToken, 'token');
    expect(session.tokenType, 'bearer');
    expect(session.user.gender, UserGender.masculino);
    expect(session.user.rol, UserRole.cliente);
    expect(session.user.isActive, isTrue);
  });
}
