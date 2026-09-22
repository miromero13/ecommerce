class AppConfig {
  const AppConfig._();

  static const backendUrl = String.fromEnvironment(
    'BACKEND_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const apiPrefix = '/api';

  static const stripePublishableKey = String.fromEnvironment(
    'STRIPE_PUBLISHABLE_KEY',
    defaultValue:
        'pk_test_51PwuiM08hp2qIPTJ9P4c108993LSovebHw9lQQeABXF3zkN71Upef4jMuPMgLPjJDWOpL5N2I94cMtze0nOxg9IP00Jo5RqrJ7',
  );

  static String get apiBaseUrl => '$backendUrl$apiPrefix';

  static const connectTimeout = Duration(seconds: 15);
  static const receiveTimeout = Duration(seconds: 15);
  static const sendTimeout = Duration(seconds: 15);
}
