import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/config/app_config.dart';

void main() {
  test('construye la URL de API con el prefijo único', () {
    expect(AppConfig.apiBaseUrl, endsWith('/api'));
    expect(AppConfig.apiBaseUrl, isNot(endsWith('/api/api')));
  });

  test('resuelve URLs relativas y externas con backendUrl', () {
    expect(AppConfig.resolveAssetUrl(null), isNull);
    expect(AppConfig.resolveAssetUrl('   '), isNull);
    expect(
      AppConfig.resolveAssetUrl('https://res.cloudinary.com/demo/image.png'),
      'https://res.cloudinary.com/demo/image.png',
    );
    expect(
      AppConfig.resolveAssetUrl('/demo-assets/catalog/blazer.png'),
      '${AppConfig.backendUrl}/demo-assets/catalog/blazer.png',
    );
    expect(
      AppConfig.resolveAssetUrl('demo-assets/catalog/blazer.png'),
      '${AppConfig.backendUrl}/demo-assets/catalog/blazer.png',
    );
  });
}
