import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../config/app_config.dart';
import 'api_exception.dart';
import 'api_response.dart';

typedef TokenProvider = String? Function();
typedef UnauthorizedHandler = void Function();

class ApiClient {
  ApiClient({Dio? dio, this.tokenProvider, this.onUnauthorized, FlutterSecureStorage? storage})
    : _dio = dio ?? _createDio(),
      _storage = storage ?? const FlutterSecureStorage();

  final Dio _dio;
  final FlutterSecureStorage _storage;
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
    Duration? receiveTimeout,
  }) {
    return _request(
      method: 'POST',
      path: path,
      data: data,
      parser: parser,
      receiveTimeout: receiveTimeout,
    );
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
    Object? data,
    T Function(dynamic value)? parser,
  }) {
    return _request(method: 'DELETE', path: path, data: data, parser: parser);
  }

  Future<ApiResponse<T>> _request<T>({
    required String method,
    required String path,
    Object? data,
    Map<String, dynamic>? queryParameters,
    T Function(dynamic value)? parser,
    Duration? receiveTimeout,
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
        options: Options(
          method: method,
          headers: headers,
          receiveTimeout: receiveTimeout,
        ),
      );
      final responseData = response.data;
      if (_cacheable(method, path) && responseData is Map) {
        await _cacheWrite(path, queryParameters, responseData);
      }

      if (responseData is! Map) {
        throw const ApiException(message: 'Respuesta inválida del servidor');
      }

      return ApiResponse.fromJson(
        Map<String, dynamic>.from(responseData),
        parser: parser,
      );
    } on DioException catch (exception) {
      // Sin internet: el catálogo se muestra con la última respuesta guardada en el dispositivo.
      if (exception.response == null && _cacheable(method, path)) {
        final cached = await _cacheRead(path, queryParameters);
        if (cached != null) {
          return ApiResponse.fromJson(cached, parser: parser);
        }
      }
      if (exception.response?.statusCode == 401) {
        onUnauthorized?.call();
      }
      throw ApiException.fromDio(exception);
    }
  }

  /// Catálogo público (productos, categorías, tallas, colores, temporadas, colecciones, sucursales): se guarda la última
  /// respuesta con conexión para poder mostrarla sin internet.
  static bool _cacheable(String method, String path) =>
      method == 'GET' && (path.startsWith('catalog/') || path == 'branches/public');

  static String _cacheKey(String path, Map<String, dynamic>? query) {
    final keys = (query?.keys.toList() ?? <String>[])..sort();
    return 'http_cache:$path?${keys.map((k) => '$k=${query![k]}').join('&')}';
  }

  Future<void> _cacheWrite(String path, Map<String, dynamic>? query, Map data) async {
    try {
      await _storage.write(key: _cacheKey(path, query), value: jsonEncode(data));
    } catch (_) {}
  }

  Future<Map<String, dynamic>?> _cacheRead(String path, Map<String, dynamic>? query) async {
    try {
      final raw = await _storage.read(key: _cacheKey(path, query));
      if (raw == null || raw.isEmpty) return null;
      final data = jsonDecode(raw);
      return data is Map ? Map<String, dynamic>.from(data) : null;
    } catch (_) {
      return null;
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
