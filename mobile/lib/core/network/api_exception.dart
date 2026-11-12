import 'package:dio/dio.dart';

class ApiException implements Exception {
  const ApiException({required this.message, this.statusCode, this.error});

  final String message;
  final int? statusCode;
  final dynamic error;

  factory ApiException.fromDio(DioException exception) {
    final responseData = exception.response?.data;

    if (responseData is Map) {
      return ApiException(
        statusCode: exception.response?.statusCode,
        message: responseData['message']?.toString() ?? 'Error de red',
        error: responseData['error'],
      );
    }

    return ApiException(
      statusCode: exception.response?.statusCode,
      // Sin respuesta del servidor: casi siempre es falta de conexión (el pago con Stripe también la requiere).
      message:
          'Sin conexión con el servidor (${_reason(exception)}). Revisa tu internet e intenta nuevamente.',
    );
  }

  static String _reason(DioException e) => switch (e.type) {
    DioExceptionType.connectionTimeout ||
    DioExceptionType.sendTimeout ||
    DioExceptionType.receiveTimeout => 'tiempo de espera agotado',
    DioExceptionType.badCertificate => 'certificado no válido, revisa la fecha del teléfono',
    DioExceptionType.cancel => 'solicitud cancelada',
    _ => e.error?.toString().split('\n').first ?? 'error de red',
  };

  @override
  String toString() => 'ApiException($statusCode): $message';
}
