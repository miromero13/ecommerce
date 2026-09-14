import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_models.dart';

void main() {
  test('inicia sesión de cliente contra el backend', () async {
    final session = await AuthApi(client: ApiClient()).login(
      const LoginRequest(
        email: 'cliente01.demo@fashionstore.bo',
        password: 'Fashion123!',
      ),
    );

    expect(session.accessToken, isNotEmpty);
    expect(session.tokenType, 'bearer');
    expect(session.user.rol, UserRole.cliente);
    expect(session.user.email, 'cliente01.demo@fashionstore.bo');
  });

  test(
    'restaura el usuario mediante users/me con el token del login',
    () async {
      final session = await AuthApi(client: ApiClient()).login(
        const LoginRequest(
          email: 'cliente01.demo@fashionstore.bo',
          password: 'Fashion123!',
        ),
      );
      final user = await AuthApi(
        client: ApiClient(tokenProvider: () => session.accessToken),
      ).currentUser();

      expect(user.id, session.user.id);
      expect(user.rol, UserRole.cliente);
      expect(user.isActive, isTrue);
    },
  );
}
