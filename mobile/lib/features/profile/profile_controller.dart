import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../auth/auth_controller.dart';
import '../auth/auth_models.dart';
import 'profile_api.dart';

enum ProfileStatus { idle, loading, saving, ready, error }

class ProfileController extends ChangeNotifier {
  ProfileController({ProfileApi? api, AuthController? authController})
    : _authController = authController,
      _api =
          api ??
          ProfileApi(
            client: ApiClient(
              tokenProvider: () => authController?.accessToken,
              onUnauthorized: authController?.handleUnauthorized,
            ),
          );

  final ProfileApi _api;
  final AuthController? _authController;

  ProfileStatus status = ProfileStatus.idle;
  User? profile;
  String? errorMessage;
  String? feedbackMessage;

  Future<void> load() => _run(_api.getProfile);

  Future<void> updateProfile({
    required String name,
    required String email,
    required UserGender gender,
  }) {
    return _run(
      () => _api.updateProfile(name: name, email: email, gender: gender),
      saving: true,
    );
  }

  Future<void> _run(
    Future<ProfileOperationResult> Function() operation, {
    bool saving = false,
  }) async {
    status = saving ? ProfileStatus.saving : ProfileStatus.loading;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();

    try {
      final result = await operation();
      if (saving && _authController != null) {
        await _authController.updateUser(result.user);
      }
      profile = result.user;
      feedbackMessage = result.message;
      status = ProfileStatus.ready;
    } catch (error) {
      status = ProfileStatus.error;
      errorMessage = error is ApiException
          ? error.message
          : 'No se pudo sincronizar el perfil.';
    }
    notifyListeners();
  }
}
