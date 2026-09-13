enum UserGender {
  masculino('masculino'),
  femenino('femenino');

  const UserGender(this.value);

  final String value;

  static UserGender fromJson(Object? value) {
    return values.firstWhere(
      (gender) => gender.value == value?.toString(),
      orElse: () => throw FormatException('Género inválido: $value'),
    );
  }
}

enum UserRole {
  administrador('administrador'),
  cliente('cliente'),
  proveedor('proveedor'),
  encargado('encargado'),
  cajero('cajero'),
  delivery('delivery');

  const UserRole(this.value);

  final String value;

  static UserRole fromJson(Object? value) {
    return values.firstWhere(
      (role) => role.value == value?.toString(),
      orElse: () => throw FormatException('Rol inválido: $value'),
    );
  }
}

class User {
  const User({
    required this.id,
    required this.name,
    required this.email,
    required this.gender,
    required this.rol,
    required this.branchId,
    required this.isActive,
  });

  final String id;
  final String name;
  final String email;
  final UserGender gender;
  final UserRole rol;
  final String? branchId;
  final bool isActive;

  factory User.fromJson(Map<String, dynamic> json) {
    final active = json['is_active'];
    if (active is! bool) {
      throw const FormatException('is_active inválido');
    }

    return User(
      id: _requiredString(json, 'id'),
      name: _requiredString(json, 'name'),
      email: _requiredString(json, 'email'),
      gender: UserGender.fromJson(json['gender']),
      rol: UserRole.fromJson(json['rol']),
      branchId: json['branch_id']?.toString(),
      isActive: active,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'gender': gender.value,
      'rol': rol.value,
      'branch_id': branchId,
      'is_active': isActive,
    };
  }
}

class LoginRequest {
  const LoginRequest({required this.email, required this.password});

  final String email;
  final String password;

  Map<String, dynamic> toJson() {
    return {
      'email': email.trim(),
      'password': password,
      'rol': UserRole.cliente.value,
    };
  }
}

class RegisterRequest {
  const RegisterRequest({
    required this.name,
    required this.email,
    required this.password,
    required this.gender,
    this.branchId,
  });

  final String name;
  final String email;
  final String password;
  final UserGender gender;
  final String? branchId;

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'email': email.trim(),
      'password': password,
      'gender': gender.value,
      if (branchId != null) 'branch_id': branchId,
    };
  }
}

class AuthSession {
  const AuthSession({
    required this.accessToken,
    required this.tokenType,
    required this.user,
  });

  final String accessToken;
  final String tokenType;
  final User user;

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    final rawUser = json['user'];
    if (rawUser is! Map) {
      throw const FormatException('user inválido');
    }

    return AuthSession(
      accessToken: _requiredString(json, 'access_token'),
      tokenType: _requiredString(json, 'token_type'),
      user: User.fromJson(Map<String, dynamic>.from(rawUser)),
    );
  }
}

String _requiredString(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null || value.toString().trim().isEmpty) {
    throw FormatException('$key inválido');
  }
  return value.toString();
}
