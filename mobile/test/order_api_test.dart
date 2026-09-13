import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/orders/order_api.dart';

void main() {
  test('lista pedidos del cliente contra el backend real', () async {
    final session = await AuthApi(client: ApiClient()).login(
      const LoginRequest(
        email: 'cliente01.demo@fashionstore.bo',
        password: 'Fashion123!',
      ),
    );
    final result = await OrderApi(
      client: ApiClient(tokenProvider: () => session.accessToken),
    ).getMine();

    expect(result.message, 'Pedidos obtenidos exitosamente');
    expect(result.orders, isA<List<dynamic>>());
  });

  test('el backend protege los pedidos sin sesión', () async {
    await expectLater(
      OrderApi().getMine(),
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
