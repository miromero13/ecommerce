import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/features/cart/cart_api.dart';

void main() {
  test('el backend rechaza agregar al carrito sin sesión', () async {
    await expectLater(
      CartApi().addItem(
        variantId: '00000000-0000-0000-0000-000000000001',
        quantity: 1,
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

  test('el backend rechaza consultar el carrito sin sesión', () async {
    await expectLater(
      CartApi().getCurrent(),
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
