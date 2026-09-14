import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/features/auth/auth_api.dart';
import 'package:mobile/features/auth/auth_models.dart';
import 'package:mobile/features/reservations/reservation_api.dart';
import 'package:mobile/features/reservations/reservation_models.dart';

void main() {
  test('lista reservas del cliente contra el backend real', () async {
    final session = await AuthApi(client: ApiClient()).login(
      const LoginRequest(
        email: 'cliente01.demo@fashionstore.bo',
        password: 'Fashion123!',
      ),
    );
    final result = await ReservationApi(
      client: ApiClient(tokenProvider: () => session.accessToken),
    ).getMine();

    expect(result.message, 'Reservas obtenidas exitosamente');
    expect(result.reservations, isA<List<dynamic>>());
  });

  test('el backend protege la creación de reservas sin sesión', () async {
    await expectLater(
      ReservationApi().create(
        branchId: '00000000-0000-0000-0000-000000000001',
        visitDate: DateTime(2026, 9, 10),
        items: const [
          ReservationDraftItem(
            variantId: '00000000-0000-0000-0000-000000000002',
            quantity: 1,
          ),
        ],
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
