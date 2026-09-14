import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/profile/profile_api.dart';

void main() {
  test('obtiene el perfil autenticado desde users/me', () async {
    final session = await AuthApi(client: ApiClient()).login(
      const LoginRequest(
        email: 'cliente01.demo@fashionstore.bo',
        password: 'Fashion123!',
      ),
    );
    final api = ProfileApi(
      client: ApiClient(tokenProvider: () => session.accessToken),
    );
    final result = await api.getProfile();

    expect(result.user.id, session.user.id);
    expect(result.user.rol, UserRole.cliente);
    expect(result.message, 'Perfil obtenido correctamente');

    final updated = await api.updateProfile(
      name: result.user.name,
      email: result.user.email,
      gender: result.user.gender,
    );
    expect(updated.user.id, result.user.id);
    expect(updated.message, 'Perfil actualizado exitosamente');
  });

  test('el backend protege la actualización del perfil sin sesión', () async {
    await expectLater(
      ProfileApi().updateProfile(
        name: 'Cliente',
        email: 'cliente@example.com',
        gender: UserGender.femenino,
      ),
      throwsA(
        isA<ApiException>().having(
          (exception) => exception.statusCode,
          'statusCode',
          403,
        ),
      ),
    );
  });
}
