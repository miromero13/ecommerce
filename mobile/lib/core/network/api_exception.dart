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
      message: exception.message ?? 'No se pudo conectar con el servidor',
    );
  }

  @override
  String toString() => 'ApiException($statusCode): $message';
}
