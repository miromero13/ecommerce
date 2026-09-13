import '../../core/network/api_client.dart';
import 'auth_models.dart';

class AuthApi {
  AuthApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<AuthSession> login(LoginRequest request) {
    return _authenticate('auth/login', request.toJson());
  }

  Future<AuthSession> register(RegisterRequest request) {
    return _authenticate('auth/register', request.toJson());
  }

  Future<User> currentUser() async {
    final response = await _client.get<User>(
      'users/me',
      parser: (value) => User.fromJson(_asMap(value)),
    );
    final user = response.data;
    if (user == null) {
      throw const FormatException('La respuesta no contiene un usuario');
    }
    return user;
  }

  Future<AuthSession> _authenticate(
    String path,
    Map<String, dynamic> data,
  ) async {
    final response = await _client.post<AuthSession>(
      path,
      data: data,
      parser: (value) => AuthSession.fromJson(_asMap(value)),
    );
    final session = response.data;
    if (session == null) {
      throw const FormatException('La respuesta no contiene una sesión');
    }
    return session;
  }

  static Map<String, dynamic> _asMap(dynamic value) {
    if (value is! Map) {
      throw const FormatException('La respuesta de autenticación es inválida');
    }
    return Map<String, dynamic>.from(value);
  }
}
