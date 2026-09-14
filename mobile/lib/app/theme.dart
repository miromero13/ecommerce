import 'package:flutter/material.dart';

abstract final class AppColors {
  static const coral = Color(0xFFDD939C);
  static const coralSoft = Color(0xFFFCEBED);
  static const slate900 = Color(0xFF202938);
  static const slate600 = Color(0xFF5C606C);
  static const slate100 = Color(0xFFF4F6FA);
  static const border = Color(0xFFE0E5EC);
  static const error = Color(0xFFBA1A1A);
  static const success = Color(0xFF28734A);
  static const warning = Color(0xFF8A5A00);
  static const white = Color(0xFFFFFFFF);
}

ThemeData buildAppTheme() {
  final colorScheme =
      ColorScheme.fromSeed(
        seedColor: AppColors.coral,
        brightness: Brightness.light,
      ).copyWith(
        primary: AppColors.coral,
        onPrimary: AppColors.slate900,
        primaryContainer: AppColors.coralSoft,
        onPrimaryContainer: AppColors.slate900,
        secondary: AppColors.slate100,
        onSecondary: AppColors.slate900,
        secondaryContainer: AppColors.coralSoft,
        onSecondaryContainer: AppColors.slate900,
        surface: AppColors.white,
        onSurface: AppColors.slate900,
        outline: AppColors.border,
        outlineVariant: AppColors.border,
        error: AppColors.error,
        onError: AppColors.white,
      );
  const radius = BorderRadius.all(Radius.circular(10));

  return ThemeData(
    useMaterial3: true,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: AppColors.white,
    appBarTheme: const AppBarThemeData(
      backgroundColor: AppColors.white,
      foregroundColor: AppColors.slate900,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: const CardThemeData(
      color: AppColors.white,
      elevation: 1,
      shadowColor: Color(0x14000000),
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    inputDecorationTheme: InputDecorationThemeData(
      filled: true,
      fillColor: AppColors.slate100,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppColors.border),
      ),
      enabledBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppColors.border),
      ),
      focusedBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppColors.coral, width: 1.5),
      ),
      errorBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppColors.error),
      ),
      focusedErrorBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppColors.error, width: 1.5),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.coral,
        foregroundColor: AppColors.slate900,
        elevation: 0,
        shape: const RoundedRectangleBorder(borderRadius: radius),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.coral,
        foregroundColor: AppColors.slate900,
        elevation: 0,
        shape: const RoundedRectangleBorder(borderRadius: radius),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.slate900,
        side: const BorderSide(color: AppColors.border),
        shape: const RoundedRectangleBorder(borderRadius: radius),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(foregroundColor: AppColors.coral),
    ),
    dividerTheme: const DividerThemeData(
      color: AppColors.border,
      thickness: 1,
      space: 1,
    ),
    dialogTheme: const DialogThemeData(
      backgroundColor: AppColors.white,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    snackBarTheme: const SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: AppColors.slate900,
      contentTextStyle: TextStyle(color: AppColors.white),
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: AppColors.white,
      indicatorColor: AppColors.coralSoft,
      labelTextStyle: WidgetStatePropertyAll(
        TextStyle(color: AppColors.slate900),
      ),
    ),
  );
}
