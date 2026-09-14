import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/storage/session_storage.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  test(
    'guarda, recupera y elimina una sesión sin guardar la contraseña',
    () async {
      const user = {
        'id': 'user-id',
        'name': 'Cliente Demo',
        'email': 'cliente@example.com',
        'gender': 'femenino',
        'branch_id': null,
        'is_active': true,
        'rol': 'cliente',
        'password': 'no-debe-guardarse',
      };
      const storage = SessionStorage();

      await storage.saveSession(
        accessToken: 'access-token',
        user: user,
        role: 'cliente',
      );

      expect(await storage.readAccessToken(), 'access-token');
      expect(await storage.readRole(), 'cliente');
      expect(await storage.readUser(), {
        'id': 'user-id',
        'name': 'Cliente Demo',
        'email': 'cliente@example.com',
        'gender': 'femenino',
        'branch_id': null,
        'is_active': true,
      });

      await storage.clear();

      expect(await storage.readAccessToken(), isNull);
      expect(await storage.readRole(), isNull);
      expect(await storage.readUser(), isNull);
    },
  );

  test('persiste la sesión devuelta por el login del backend', () async {
    final response = await ApiClient().post<dynamic>(
      'auth/login',
      data: {
        'email': 'cliente01.demo@fashionstore.bo',
        'password': 'Fashion123!',
        'rol': 'cliente',
      },
    );
    final data = Map<String, dynamic>.from(response.data as Map);
    final user = Map<String, dynamic>.from(data['user'] as Map);

    const storage = SessionStorage();
    await storage.saveSession(
      accessToken: data['access_token'] as String,
      user: user,
      role: user['rol'] as String,
    );

    expect(await storage.readAccessToken(), isNotEmpty);
    expect(await storage.readRole(), 'cliente');
    expect((await storage.readUser())?['email'], user['email']);
    expect((await storage.readUser())?.containsKey('password'), isFalse);
  });
}
