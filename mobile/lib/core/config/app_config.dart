class AppConfig {
  const AppConfig._();

  static const backendUrl = String.fromEnvironment(
    'BACKEND_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  static const apiPrefix = '/api';

  static String get apiBaseUrl => '$backendUrl$apiPrefix';

  static const connectTimeout = Duration(seconds: 15);
  static const receiveTimeout = Duration(seconds: 15);
  static const sendTimeout = Duration(seconds: 15);
}
