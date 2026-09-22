import 'package:flutter/material.dart';

import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/app_text_field.dart';
import '../auth/auth_controller.dart';
import '../auth/auth_models.dart';
import '../auth/login_dialog.dart';
import 'profile_controller.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key, required this.authController, this.controller});

  final AuthController authController;
  final ProfileController? controller;

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  late final ProfileController _controller;
  late final bool _ownsController;
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();

  String? _loadedToken;
  String? _formProfileId;
  UserGender _gender = UserGender.femenino;
  String? _validationError;
  bool _editing = false;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller =
        widget.controller ??
        ProfileController(authController: widget.authController);
    widget.authController.addListener(_handleAuthChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) => _handleAuthChanged());
  }

  @override
  void dispose() {
    widget.authController.removeListener(_handleAuthChanged);
    _nameController.dispose();
    _emailController.dispose();
    if (_ownsController) _controller.dispose();
    super.dispose();
  }

  void _handleAuthChanged() {
    if (!mounted) return;
    if (!widget.authController.isAuthenticated) {
      _loadedToken = null;
      _editing = false;
      return;
    }

    final token = widget.authController.accessToken;
    if (token == null || token == _loadedToken) return;
    _loadedToken = token;
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    await _controller.load();
    if (!mounted || _controller.profile == null) return;
    _syncForm(_controller.profile!);
  }

  void _syncForm(User user) {
    _nameController.text = user.name;
    _emailController.text = user.email;
    _gender = user.gender;
    _formProfileId = user.id;
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.authController,
      builder: (context, _) {
        if (widget.authController.status == AuthStatus.loading) {
          return const AppLoading(message: 'Validando sesión...');
        }
        if (widget.authController.status == AuthStatus.error) {
          return AppErrorView(
            message:
                widget.authController.errorMessage ??
                'No se pudo validar la sesión.',
            onRetry: widget.authController.restoreSession,
          );
        }
        if (!widget.authController.isAuthenticated) {
          return AppEmptyView(
            title: 'Cuenta privada',
            message: 'Inicia sesión para consultar y editar tu perfil.',
            actionLabel: 'Iniciar sesión',
            onAction: () => LoginDialog.show(
              context: context,
              controller: widget.authController,
            ),
          );
        }

        return ListenableBuilder(
          listenable: _controller,
          builder: (context, _) => _buildProfile(context),
        );
      },
    );
  }

  Widget _buildProfile(BuildContext context) {
    final profile = _controller.profile;
    if (profile == null && _controller.status == ProfileStatus.error) {
      return AppErrorView(
        message: _controller.errorMessage ?? 'No se pudo cargar el perfil.',
        onRetry: _loadProfile,
      );
    }
    if (profile == null) {
      return const AppLoading(message: 'Cargando perfil...');
    }

    if (_formProfileId != profile.id) _syncForm(profile);
    final isSaving = _controller.status == ProfileStatus.saving;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      children: [
        AppSectionTitle(
          title: 'Mi cuenta',
          subtitle: 'Administra la información de tu perfil.',
        ),
        const SizedBox(height: 16),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (_editing) _editForm(isSaving) else _readOnlyProfile(profile),
              if (_controller.errorMessage != null) ...[
                const SizedBox(height: 12),
                Text(
                  _controller.errorMessage!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: 16),
        const SizedBox(height: 16),
        AppButton(
          label: 'Cerrar sesión',
          icon: const Icon(Icons.logout),
          variant: AppButtonVariant.outlined,
          onPressed: isSaving ? null : _logout,
          expand: true,
        ),
      ],
    );
  }

  Widget _readOnlyProfile(User profile) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _ProfileRow(label: 'Nombre', value: profile.name),
        _ProfileRow(label: 'Correo electrónico', value: profile.email),
        _ProfileRow(label: 'Género', value: _genderLabel(profile.gender)),
        const SizedBox(height: 12),
        AppButton(
          label: 'Editar perfil',
          icon: const Icon(Icons.edit_outlined),
          variant: AppButtonVariant.outlined,
          onPressed: () => setState(() {
            _editing = true;
            _validationError = null;
          }),
          expand: true,
        ),
      ],
    );
  }

  Widget _editForm(bool isSaving) {
    return Column(
      children: [
        AppTextField(
          label: 'Nombre',
          controller: _nameController,
          enabled: !isSaving,
        ),
        const SizedBox(height: 12),
        AppTextField(
          label: 'Correo electrónico',
          controller: _emailController,
          enabled: !isSaving,
          keyboardType: TextInputType.emailAddress,
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<UserGender>(
          initialValue: _gender,
          decoration: const InputDecoration(labelText: 'Género'),
          isExpanded: true,
          items: [
            for (final gender in UserGender.values)
              DropdownMenuItem(
                value: gender,
                child: Text(_genderLabel(gender)),
              ),
          ],
          onChanged: isSaving
              ? null
              : (value) {
                  if (value != null) setState(() => _gender = value);
                },
        ),
        if (_validationError != null) ...[
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              _validationError!,
              style: TextStyle(color: Colors.red.shade700),
            ),
          ),
        ],
        const SizedBox(height: 16),
        OverflowBar(
          spacing: 8,
          overflowSpacing: 8,
          alignment: MainAxisAlignment.spaceBetween,
          children: [
            AppButton(
              label: 'Cancelar',
              variant: AppButtonVariant.text,
              onPressed: isSaving ? null : _cancelEditing,
            ),
            AppButton(
              label: 'Guardar',
              icon: const Icon(Icons.check),
              onPressed: isSaving ? null : _saveProfile,
              isLoading: isSaving,
            ),
          ],
        ),
      ],
    );
  }

  void _cancelEditing() {
    final profile = _controller.profile;
    if (profile == null) return;
    setState(() {
      _editing = false;
      _validationError = null;
      _syncForm(profile);
    });
  }

  Future<void> _saveProfile() async {
    final name = _nameController.text.trim();
    final email = _emailController.text.trim();
    if (name.isEmpty) {
      setState(() => _validationError = 'Ingresa tu nombre.');
      return;
    }
    if (!email.contains('@')) {
      setState(() => _validationError = 'Ingresa un correo válido.');
      return;
    }

    setState(() => _validationError = null);
    await _controller.updateProfile(name: name, email: email, gender: _gender);
    if (!mounted) return;
    if (_controller.status == ProfileStatus.ready) {
      setState(() {
        _editing = false;
        _syncForm(_controller.profile!);
      });
      final message = _controller.feedbackMessage;
      if (message != null) {
        AppSnackBar.show(context, message, tone: AppSnackBarTone.success);
      }
    }
  }

  Future<void> _logout() => widget.authController.logout();

  static String _genderLabel(UserGender gender) {
    return switch (gender) {
      UserGender.masculino => 'Masculino',
      UserGender.femenino => 'Femenino',
    };
  }
}

class _ProfileRow extends StatelessWidget {
  const _ProfileRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelMedium),
          const SizedBox(height: 2),
          Text(value, style: Theme.of(context).textTheme.bodyLarge),
        ],
      ),
    );
  }
}
