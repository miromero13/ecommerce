import 'dart:io' show Platform;

import 'package:flutter/foundation.dart' show kIsWeb;

class AppConfig {
  const AppConfig._();

  static const _envBackendUrl = String.fromEnvironment('BACKEND_URL');

  /// Resolves the backend base URL:
  /// - Environment override if passed via --dart-define=BACKEND_URL=...
  /// - On Android Emulator: http://10.0.2.2:8000 (points to host localhost)
  /// - On iOS Simulator / Desktop: http://127.0.0.1:8000
  static String get backendUrl {
    if (_envBackendUrl.isNotEmpty) {
      return _envBackendUrl;
    }
    if (!kIsWeb && Platform.isAndroid) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  // The emulator default targets the local frontend; deployed/device builds
  // must provide a real HTTPS URL with --dart-define=FRONTEND_URL=....
  static const frontendUrl = String.fromEnvironment(
    'FRONTEND_URL',
    defaultValue: 'https://ecommerce-five-xi-60.vercel.app',
  );

  static const decartApiKey = String.fromEnvironment('DECART_API_KEY');

  static const apiPrefix = '/api';

  static const stripePublishableKey = String.fromEnvironment(
    'STRIPE_PUBLISHABLE_KEY',
    defaultValue:
        'pk_test_51PwuiM08hp2qIPTJ9P4c108993LSovebHw9lQQeABXF3zkN71Upef4jMuPMgLPjJDWOpL5N2I94cMtze0nOxg9IP00Jo5RqrJ7',
  );

  static String get apiBaseUrl => '$backendUrl$apiPrefix';

  static String get decartTryOnUrl =>
      '${frontendUrl.trim().replaceFirst(RegExp(r'/$'), '')}/decart-try-on.html';

  static const connectTimeout = Duration(seconds: 15);
  static const receiveTimeout = Duration(seconds: 15);
  static const sendTimeout = Duration(seconds: 15);
}
