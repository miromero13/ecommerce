import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SessionStorage {
  const SessionStorage({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'access_token';
  static const _userKey = 'session_user';
  static const _roleKey = 'session_role';
  static const _cartBranchIdKey = 'cart_branch_id';
  static const _cartBranchNameKey = 'cart_branch_name';
  static const _cartTenantNameKey = 'cart_tenant_name';

  final FlutterSecureStorage _storage;

  Future<void> saveCartContext({
    required String branchId,
    required String branchName,
    required String tenantName,
  }) async {
    await _storage.write(key: _cartBranchIdKey, value: branchId);
    await _storage.write(key: _cartBranchNameKey, value: branchName);
    await _storage.write(key: _cartTenantNameKey, value: tenantName);
  }

  Future<Map<String, String>?> readCartContext() async {
    final branchId = await _storage.read(key: _cartBranchIdKey);
    if (branchId == null || branchId.isEmpty) return null;
    final branchName = await _storage.read(key: _cartBranchNameKey) ?? '';
    final tenantName = await _storage.read(key: _cartTenantNameKey) ?? '';
    return {
      'branch_id': branchId,
      'branch_name': branchName,
      'tenant_name': tenantName,
    };
  }

  Future<void> clearCartContext() async {
    await Future.wait([
      _storage.delete(key: _cartBranchIdKey),
      _storage.delete(key: _cartBranchNameKey),
      _storage.delete(key: _cartTenantNameKey),
    ]);
  }

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
      _storage.delete(key: _cartBranchIdKey),
      _storage.delete(key: _cartBranchNameKey),
      _storage.delete(key: _cartTenantNameKey),
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
