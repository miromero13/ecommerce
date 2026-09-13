import 'package:dio/dio.dart';

import '../config/app_config.dart';
import 'api_exception.dart';
import 'api_response.dart';

typedef TokenProvider = String? Function();
typedef UnauthorizedHandler = void Function();

class ApiClient {
  ApiClient({Dio? dio, this.tokenProvider, this.onUnauthorized})
    : _dio = dio ?? _createDio();

  final Dio _dio;
  final TokenProvider? tokenProvider;
  final UnauthorizedHandler? onUnauthorized;

  Future<ApiResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    T Function(dynamic value)? parser,
  }) {
    return _request(
      method: 'GET',
      path: path,
      queryParameters: queryParameters,
      parser: parser,
    );
  }

  Future<ApiResponse<T>> post<T>(
    String path, {
    Object? data,
    T Function(dynamic value)? parser,
  }) {
    return _request(method: 'POST', path: path, data: data, parser: parser);
  }

  Future<ApiResponse<T>> patch<T>(
    String path, {
    Object? data,
    T Function(dynamic value)? parser,
  }) {
    return _request(method: 'PATCH', path: path, data: data, parser: parser);
  }

  Future<ApiResponse<T>> put<T>(
    String path, {
    Object? data,
    T Function(dynamic value)? parser,
  }) {
    return _request(method: 'PUT', path: path, data: data, parser: parser);
  }

  Future<ApiResponse<T>> delete<T>(
    String path, {
    T Function(dynamic value)? parser,
  }) {
    return _request(method: 'DELETE', path: path, parser: parser);
  }

  Future<ApiResponse<T>> _request<T>({
    required String method,
    required String path,
    Object? data,
    Map<String, dynamic>? queryParameters,
    T Function(dynamic value)? parser,
  }) async {
    final token = tokenProvider?.call();
    final headers = <String, dynamic>{'Accept': 'application/json'};

    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }

    try {
      final response = await _dio.request<dynamic>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: Options(method: method, headers: headers),
      );
      final responseData = response.data;

      if (responseData is! Map) {
        throw const ApiException(message: 'Respuesta inválida del servidor');
      }

      return ApiResponse.fromJson(
        Map<String, dynamic>.from(responseData),
        parser: parser,
      );
    } on DioException catch (exception) {
      if (exception.response?.statusCode == 401) {
        onUnauthorized?.call();
      }
      throw ApiException.fromDio(exception);
    }
  }

  static Dio _createDio() {
    return Dio(
      BaseOptions(
        baseUrl: '${AppConfig.apiBaseUrl}/',
        connectTimeout: AppConfig.connectTimeout,
        receiveTimeout: AppConfig.receiveTimeout,
        sendTimeout: AppConfig.sendTimeout,
        responseType: ResponseType.json,
      ),
    );
  }
}
