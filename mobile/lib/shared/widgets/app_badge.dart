import 'package:flutter/material.dart';

import '../../app/theme.dart';

enum AppBadgeTone { neutral, accent, success, warning, error }

class AppBadge extends StatelessWidget {
  const AppBadge({
    super.key,
    required this.label,
    this.tone = AppBadgeTone.neutral,
  });

  final String label;
  final AppBadgeTone tone;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final (background, foreground) = switch (tone) {
      AppBadgeTone.neutral => (
        colorScheme.surfaceContainerHighest,
        colorScheme.onSurfaceVariant,
      ),
      AppBadgeTone.accent => (
        colorScheme.primaryContainer,
        colorScheme.onPrimaryContainer,
      ),
      AppBadgeTone.success => (
        AppColors.success.withValues(alpha: 0.12),
        AppColors.success,
      ),
      AppBadgeTone.warning => (
        AppColors.warning.withValues(alpha: 0.12),
        AppColors.warning,
      ),
      AppBadgeTone.error => (
        colorScheme.errorContainer,
        colorScheme.onErrorContainer,
      ),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelMedium?.copyWith(
          color: foreground,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
