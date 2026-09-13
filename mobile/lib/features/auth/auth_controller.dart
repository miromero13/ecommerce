import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/storage/session_storage.dart';
import 'auth_api.dart';
import 'auth_models.dart';

enum AuthStatus { loading, guest, authenticated, error }

class AuthController extends ChangeNotifier {
  AuthController({AuthApi? api, SessionStorage? storage})
    : _storage = storage ?? const SessionStorage() {
    _api =
        api ??
        AuthApi(
          client: ApiClient(
            tokenProvider: () => _accessToken,
            onUnauthorized: _handleUnauthorized,
          ),
        );
  }

  final SessionStorage _storage;
  late final AuthApi _api;

  AuthStatus _status = AuthStatus.loading;
  User? _user;
  String? _accessToken;
  String? _errorMessage;
  bool _guestAccess = false;

  AuthStatus get status => _status;
  User? get user => _user;
  String? get accessToken => _accessToken;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  bool get hasGuestAccess => _guestAccess;

  void handleUnauthorized() => _handleUnauthorized();

  void continueAsGuest() {
    _guestAccess = true;
    _setState(AuthStatus.guest);
  }

  Future<void> restoreSession() async {
    _guestAccess = false;
    _setState(AuthStatus.loading);

    try {
      final token = await _storage.readAccessToken();
      if (token == null || token.trim().isEmpty) {
        _clearMemory();
        _setState(AuthStatus.guest);
        return;
      }

      _accessToken = token;
      final user = await _api.currentUser();
      if (!_isMobileClient(user)) {
        await _clearPersistedSession();
        _clearMemory();
        _setState(AuthStatus.guest);
        return;
      }

      await _storage.saveSession(
        accessToken: token,
        user: user.toJson(),
        role: user.rol.value,
      );
      _user = user;
      _setState(AuthStatus.authenticated);
    } on ApiException catch (exception) {
      if (exception.statusCode == 401) {
        await _clearPersistedSession();
        _clearMemory();
        _setState(AuthStatus.guest);
        return;
      }
      _setState(AuthStatus.error, errorMessage: exception.message);
    } catch (exception) {
      _setState(AuthStatus.error, errorMessage: exception.toString());
    }
  }

  Future<bool> login(LoginRequest request) async {
    _guestAccess = false;
    _setState(AuthStatus.loading);
    try {
      return await _saveSession(await _api.login(request));
    } on ApiException catch (exception) {
      _setState(AuthStatus.error, errorMessage: exception.message);
      return false;
    } catch (exception) {
      _setState(AuthStatus.error, errorMessage: exception.toString());
      return false;
    }
  }

  Future<bool> register(RegisterRequest request) async {
    _guestAccess = false;
    _setState(AuthStatus.loading);
    try {
      return await _saveSession(await _api.register(request));
    } on ApiException catch (exception) {
      _setState(AuthStatus.error, errorMessage: exception.message);
      return false;
    } catch (exception) {
      _setState(AuthStatus.error, errorMessage: exception.toString());
      return false;
    }
  }

  Future<void> logout() async {
    _guestAccess = false;
    await _clearPersistedSession();
    _clearMemory();
    _setState(AuthStatus.guest);
  }

  Future<void> updateUser(User user) async {
    if (!_isMobileClient(user) || _accessToken == null) {
      throw StateError('No existe una sesión de cliente activa.');
    }
    await _storage.saveSession(
      accessToken: _accessToken!,
      user: user.toJson(),
      role: user.rol.value,
    );
    _user = user;
    _setState(AuthStatus.authenticated);
  }

  Future<bool> _saveSession(AuthSession session) async {
    if (!_isMobileClient(session.user)) {
      await _clearPersistedSession();
      _clearMemory();
      _setState(
        AuthStatus.error,
        errorMessage: 'La sesión no pertenece a un cliente activo.',
      );
      return false;
    }

    await _storage.saveSession(
      accessToken: session.accessToken,
      user: session.user.toJson(),
      role: session.user.rol.value,
    );
    _accessToken = session.accessToken;
    _user = session.user;
    _setState(AuthStatus.authenticated);
    return true;
  }

  bool _isMobileClient(User user) {
    return user.rol == UserRole.cliente && user.isActive;
  }

  void _handleUnauthorized() {
    _guestAccess = false;
    _clearMemory();
    _setState(AuthStatus.guest);
    unawaited(_clearPersistedSession());
  }

  Future<void> _clearPersistedSession() => _storage.clear();

  void _clearMemory() {
    _accessToken = null;
    _user = null;
  }

  void _setState(AuthStatus status, {String? errorMessage}) {
    _status = status;
    _errorMessage = errorMessage;
    notifyListeners();
  }
}
