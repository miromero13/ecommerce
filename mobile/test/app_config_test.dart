import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/config/app_config.dart';

void main() {
  test('construye la URL de API con el prefijo único', () {
    expect(AppConfig.apiBaseUrl, endsWith('/api'));
    expect(AppConfig.apiBaseUrl, isNot(endsWith('/api/api')));
  });
}
