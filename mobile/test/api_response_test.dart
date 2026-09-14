import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_response.dart';

void main() {
  test('parsea una respuesta exitosa y transforma data', () {
    final response = ApiResponse<int>.fromJson({
      'statusCode': 200,
      'message': 'Correcto',
      'data': {'value': 42},
      'countData': 1,
    }, parser: (value) => (value as Map<String, dynamic>)['value'] as int);

    expect(response.statusCode, 200);
    expect(response.message, 'Correcto');
    expect(response.data, 42);
    expect(response.countData, 1);
  });

  test('conserva message y error en una respuesta fallida', () {
    final response = ApiResponse<dynamic>.fromJson({
      'statusCode': 422,
      'message': 'Error de validación',
      'error': ['El campo es obligatorio'],
    });

    expect(response.statusCode, 422);
    expect(response.message, 'Error de validación');
    expect(response.error, ['El campo es obligatorio']);
    expect(response.data, isNull);
  });
}
