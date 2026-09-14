import 'package:flutter/material.dart';

import 'auth_controller.dart';
import 'login_page.dart';

abstract final class LoginDialog {
  static Future<bool?> show({
    required BuildContext context,
    required AuthController controller,
  }) {
    return showDialog<bool>(
      context: context,
      builder: (_) => Dialog(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: LoginPage(controller: controller),
        ),
      ),
    );
  }
}
