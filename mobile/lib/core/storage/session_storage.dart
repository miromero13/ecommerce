import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SessionStorage {
  const SessionStorage({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'access_token';
  static const _userKey = 'session_user';
  static const _roleKey = 'session_role';

  final FlutterSecureStorage _storage;

  Future<void> saveSession({
    required String accessToken,
    required Map<String, dynamic> user,
    required String role,
  }) async {
    if (accessToken.trim().isEmpty) {
      throw ArgumentError.value(accessToken, 'accessToken');
    }
    if (role.trim().isEmpty) {
      throw ArgumentError.value(role, 'role');
    }

    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _userKey, value: jsonEncode(_minimalUser(user)));
    await _storage.write(key: _roleKey, value: role);
  }

  Future<String?> readAccessToken() {
    return _storage.read(key: _accessTokenKey);
  }

  Future<String?> readRole() {
    return _storage.read(key: _roleKey);
  }

  Future<Map<String, dynamic>?> readUser() async {
    final value = await _storage.read(key: _userKey);
    if (value == null) {
      return null;
    }

    try {
      final decoded = jsonDecode(value);
      return decoded is Map ? Map<String, dynamic>.from(decoded) : null;
    } on FormatException {
      return null;
    }
  }

  Future<void> clear() async {
    await Future.wait([
      _storage.delete(key: _accessTokenKey),
      _storage.delete(key: _userKey),
      _storage.delete(key: _roleKey),
    ]);
  }

  static Map<String, dynamic> _minimalUser(Map<String, dynamic> user) {
    const fields = ['id', 'name', 'email', 'gender', 'branch_id', 'is_active'];

    return {
      for (final field in fields)
        if (user.containsKey(field)) field: user[field],
    };
  }
}
