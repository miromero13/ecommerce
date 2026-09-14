import '../../core/network/api_client.dart';
import '../auth/auth_models.dart';

class ProfileApi {
  ProfileApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<ProfileOperationResult> getProfile() async {
    final response = await _client.get<User>('users/me', parser: _parseUser);
    return _result(response.data, response.message);
  }

  Future<ProfileOperationResult> updateProfile({
    required String name,
    required String email,
    required UserGender gender,
  }) async {
    final response = await _client.put<User>(
      'users/me',
      data: {
        'name': name.trim(),
        'email': email.trim(),
        'gender': gender.value,
      },
      parser: _parseUser,
    );
    return _result(response.data, response.message);
  }

  static User _parseUser(dynamic value) {
    if (value is! Map) {
      throw const FormatException('La respuesta del perfil es inválida');
    }
    return User.fromJson(Map<String, dynamic>.from(value));
  }

  static ProfileOperationResult _result(User? user, String message) {
    if (user == null) {
      throw const FormatException('La respuesta no contiene un perfil');
    }
    return ProfileOperationResult(user: user, message: message);
  }
}

class ProfileOperationResult {
  const ProfileOperationResult({required this.user, required this.message});

  final User user;
  final String message;
}
