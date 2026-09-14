import 'package:flutter/material.dart';

import '../../app/theme.dart';

enum AppSnackBarTone { neutral, success, warning, error }

abstract final class AppSnackBar {
  static void show(
    BuildContext context,
    String message, {
    AppSnackBarTone tone = AppSnackBarTone.neutral,
    String? actionLabel,
    VoidCallback? onAction,
    Duration duration = const Duration(seconds: 3),
  }) {
    final backgroundColor = switch (tone) {
      AppSnackBarTone.neutral => null,
      AppSnackBarTone.success => AppColors.success,
      AppSnackBarTone.warning => AppColors.warning,
      AppSnackBarTone.error => AppColors.error,
    };

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: backgroundColor,
          duration: duration,
          action: actionLabel != null && onAction != null
              ? SnackBarAction(label: actionLabel, onPressed: onAction)
              : null,
        ),
      );
  }
}
