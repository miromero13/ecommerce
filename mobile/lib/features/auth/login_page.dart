import 'package:flutter/material.dart';

import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_icon_button.dart';
import '../../shared/widgets/app_text_field.dart';
import 'auth_controller.dart';
import 'auth_models.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({
    super.key,
    required this.controller,
    this.showCloseButton = true,
    this.showGuestButton = false,
    this.centerContent = false,
    this.onGuest,
  });

  final AuthController controller;
  final bool showCloseButton;
  final bool showGuestButton;
  final bool centerContent;
  final VoidCallback? onGuest;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  UserGender _gender = UserGender.femenino;
  bool _registering = false;
  bool _obscurePassword = true;
  bool _submitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final title = _registering ? 'Crear cuenta' : 'Iniciar sesión';
    final errorMessage = _errorMessage ?? widget.controller.errorMessage;

    return LayoutBuilder(
      builder: (context, constraints) => SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
        child: ConstrainedBox(
          constraints: BoxConstraints(
            minHeight: widget.centerContent ? constraints.maxHeight - 48 : 0,
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        title,
                        style: Theme.of(context).textTheme.headlineSmall
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                    ),
                    if (widget.showCloseButton)
                      AppIconButton(
                        icon: Icons.close,
                        tooltip: 'Cerrar',
                        onPressed: _submitting
                            ? null
                            : () => Navigator.pop(context),
                      ),
                  ],
                ),
                const SizedBox(height: 20),
                if (_registering) ...[
                  AppTextField(
                    label: 'Nombre',
                    controller: _nameController,
                    enabled: !_submitting,
                    textInputAction: TextInputAction.next,
                  ),
                  const SizedBox(height: 12),
                ],
                AppTextField(
                  label: 'Correo electrónico',
                  controller: _emailController,
                  enabled: !_submitting,
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                ),
                const SizedBox(height: 12),
                AppTextField(
                  label: 'Contraseña',
                  controller: _passwordController,
                  enabled: !_submitting,
                  obscureText: _obscurePassword,
                  textInputAction: TextInputAction.done,
                  suffixIcon: IconButton(
                    onPressed: _submitting
                        ? null
                        : () => setState(
                            () => _obscurePassword = !_obscurePassword,
                          ),
                    icon: Icon(
                      _obscurePassword
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                    ),
                    tooltip: _obscurePassword
                        ? 'Mostrar contraseña'
                        : 'Ocultar contraseña',
                  ),
                ),
                if (_registering) ...[
                  const SizedBox(height: 12),
                  DropdownButtonFormField<UserGender>(
                    initialValue: _gender,
                    decoration: const InputDecoration(labelText: 'Género'),
                    items: [
                      for (final gender in UserGender.values)
                        DropdownMenuItem(
                          value: gender,
                          child: Text(_genderLabel(gender)),
                        ),
                    ],
                    onChanged: _submitting
                        ? null
                        : (value) {
                            if (value != null) setState(() => _gender = value);
                          },
                  ),
                ],
                if (errorMessage != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    errorMessage,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
                const SizedBox(height: 20),
                AppButton(
                  label: title,
                  onPressed: _submitting ? null : _submit,
                  isLoading: _submitting,
                  expand: true,
                ),
                const SizedBox(height: 8),
                AppButton(
                  label: _registering
                      ? 'Ya tengo una cuenta'
                      : 'Crear una cuenta',
                  variant: AppButtonVariant.text,
                  onPressed: _submitting
                      ? null
                      : () => setState(() {
                          _registering = !_registering;
                          _errorMessage = null;
                        }),
                  expand: true,
                ),
                if (widget.showGuestButton) ...[
                  const SizedBox(height: 8),
                  AppButton(
                    label: 'Entrar como invitado',
                    variant: AppButtonVariant.outlined,
                    onPressed: _submitting ? null : _continueAsGuest,
                    expand: true,
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _continueAsGuest() {
    widget.controller.continueAsGuest();
    widget.onGuest?.call();
  }

  Future<void> _submit() async {
    final validationError = _validate();
    if (validationError != null) {
      setState(() => _errorMessage = validationError);
      return;
    }

    setState(() {
      _submitting = true;
      _errorMessage = null;
    });

    final success = _registering
        ? await widget.controller.register(
            RegisterRequest(
              name: _nameController.text,
              email: _emailController.text,
              password: _passwordController.text,
              gender: _gender,
            ),
          )
        : await widget.controller.login(
            LoginRequest(
              email: _emailController.text,
              password: _passwordController.text,
            ),
          );

    if (!mounted) return;
    if (success) {
      Navigator.of(context).pop(true);
      return;
    }

    setState(() {
      _submitting = false;
      _errorMessage =
          widget.controller.errorMessage ?? 'No se pudo autenticar.';
    });
  }

  String? _validate() {
    if (_registering && _nameController.text.trim().isEmpty) {
      return 'Ingresa tu nombre.';
    }
    if (!_emailController.text.trim().contains('@')) {
      return 'Ingresa un correo válido.';
    }
    if (_passwordController.text.isEmpty) {
      return 'Ingresa tu contraseña.';
    }
    return null;
  }

  static String _genderLabel(UserGender gender) {
    return switch (gender) {
      UserGender.masculino => 'Masculino',
      UserGender.femenino => 'Femenino',
    };
  }
}
