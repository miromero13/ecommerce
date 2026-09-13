import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/network/api_exception.dart';

void main() {
  test('obtiene el catálogo público con Dio', () async {
    final response = await ApiClient().get<dynamic>('catalog/products');

    expect(response.statusCode, 200);
    expect(response.message, isNotEmpty);
    expect(response.data, isA<List<dynamic>>());
  });

  test('convierte una validación del backend en ApiException', () async {
    await expectLater(
      ApiClient().get<dynamic>('catalog/availability'),
      throwsA(
        isA<ApiException>().having(
          (exception) => exception.statusCode,
          'statusCode',
          422,
        ),
      ),
    );
  });

  test('convierte la falta de autenticación en ApiException', () async {
    await expectLater(
      ApiClient().get<dynamic>('cart/current'),
      throwsA(
        isA<ApiException>().having(
          (exception) => exception.statusCode,
          'statusCode',
          403,
        ),
      ),
    );
  });

  test('ejecuta el callback cuando el backend responde 401', () async {
    var unauthorized = false;
    final client = ApiClient(
      tokenProvider: () => 'token-invalido',
      onUnauthorized: () => unauthorized = true,
    );

    await expectLater(
      client.get<dynamic>('users/me'),
      throwsA(
        isA<ApiException>().having(
          (exception) => exception.statusCode,
          'statusCode',
          401,
        ),
      ),
    );
    expect(unauthorized, isTrue);
  });
}
