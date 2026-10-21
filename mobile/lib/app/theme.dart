import 'package:flutter/material.dart';

abstract final class AppColors {
  // Light palette tokens (:root)
  static const background = Color(0xFFFFFFFF);
  static const foreground = Color(0xFF1C2124);
  static const card = Color(0xFFFFFFFF);
  static const cardForeground = Color(0xFF1C2124);
  static const popover = Color(0xFFFFFFFF);
  static const popoverForeground = Color(0xFF1C2124);
  static const primary = Color(0xFF007F82);
  static const primaryForeground = Color(0xFFEBFDFB);
  static const secondary = Color(0xFFF6F5F6);
  static const secondaryForeground = Color(0xFF2D2C2E);
  static const muted = Color(0xFFF3F5F5);
  static const mutedForeground = Color(0xFF6E7D82);
  static const accent = Color(0xFFF3F5F5);
  static const accentForeground = Color(0xFF2D3437);
  static const destructive = Color(0xFFE12739);
  static const border = Color(0xFFE6EBEC);
  static const input = Color(0xFFE6EBEC);
  static const ring = Color(0xFF9CAAB0);

  // Charts
  static const chart1 = Color(0xFF64E3D4);
  static const chart2 = Color(0xFF24B9B4);
  static const chart3 = Color(0xFF009D9E);
  static const chart4 = Color(0xFF007F82);
  static const chart5 = Color(0xFF00666A);

  // Sidebar
  static const sidebar = Color(0xFFFAFBFB);
  static const sidebarForeground = Color(0xFF1C2124);
  static const sidebarPrimary = Color(0xFF009D9E);
  static const sidebarPrimaryForeground = Color(0xFFEBFDFB);
  static const sidebarAccent = Color(0xFFF3F5F5);
  static const sidebarAccentForeground = Color(0xFF2D3437);
  static const sidebarBorder = Color(0xFFE6EBEC);
  static const sidebarRing = Color(0xFF9CAAB0);

  // Status & utilities
  static const error = destructive;
  static const success = Color(0xFF28734A);
  static const warning = Color(0xFF8A5A00);
  static const white = Color(0xFFFFFFFF);

  // Backward compatibility aliases
  static const coral = primary;
  static const coralSoft = primaryForeground;
  static const slate900 = foreground;
  static const slate600 = mutedForeground;
  static const slate100 = muted;
}

abstract final class AppDarkColors {
  // Dark palette tokens (.dark)
  static const background = Color(0xFF1C2124);
  static const foreground = Color(0xFFFAFBFB);
  static const card = Color(0xFF2D3437);
  static const cardForeground = Color(0xFFFAFBFB);
  static const popover = Color(0xFF2D3437);
  static const popoverForeground = Color(0xFFFAFBFB);
  static const primary = Color(0xFF00666A);
  static const primaryForeground = Color(0xFFEBFDFB);
  static const secondary = Color(0xFF3B3A3C);
  static const secondaryForeground = Color(0xFFFAFAFA);
  static const muted = Color(0xFF3A4245);
  static const mutedForeground = Color(0xFF9CAAB0);
  static const accent = Color(0xFF3A4245);
  static const accentForeground = Color(0xFFFAFBFB);
  static const destructive = Color(0xFFFF6060);
  static const border = Color(0x1AFFFFFF);
  static const input = Color(0x26FFFFFF);
  static const ring = Color(0xFF6E7D82);

  // Charts
  static const chart1 = Color(0xFF64E3D4);
  static const chart2 = Color(0xFF24B9B4);
  static const chart3 = Color(0xFF009D9E);
  static const chart4 = Color(0xFF007F82);
  static const chart5 = Color(0xFF00666A);

  // Sidebar
  static const sidebar = Color(0xFF2D3437);
  static const sidebarForeground = Color(0xFFFAFBFB);
  static const sidebarPrimary = Color(0xFF24B9B4);
  static const sidebarPrimaryForeground = Color(0xFF193F40);
  static const sidebarAccent = Color(0xFF3A4245);
  static const sidebarAccentForeground = Color(0xFFFAFBFB);
  static const sidebarBorder = Color(0x1AFFFFFF);
  static const sidebarRing = Color(0xFF6E7D82);

  // Status & utilities
  static const error = destructive;
  static const success = Color(0xFF28734A);
  static const warning = Color(0xFF8A5A00);
}

ThemeData buildAppTheme() {
  final colorScheme =
      ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        brightness: Brightness.light,
      ).copyWith(
        primary: AppColors.primary,
        onPrimary: AppColors.primaryForeground,
        primaryContainer: AppColors.primaryForeground,
        onPrimaryContainer: AppColors.primary,
        secondary: AppColors.secondary,
        onSecondary: AppColors.secondaryForeground,
        secondaryContainer: AppColors.accent,
        onSecondaryContainer: AppColors.accentForeground,
        surface: AppColors.background,
        onSurface: AppColors.foreground,
        outline: AppColors.border,
        outlineVariant: AppColors.border,
        error: AppColors.error,
        onError: AppColors.white,
      );
  const radius = BorderRadius.all(Radius.circular(10));

  return ThemeData(
    useMaterial3: true,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: AppColors.background,
    appBarTheme: const AppBarThemeData(
      backgroundColor: AppColors.background,
      foregroundColor: AppColors.foreground,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: const CardThemeData(
      color: AppColors.card,
      elevation: 1,
      shadowColor: Color(0x14000000),
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    inputDecorationTheme: InputDecorationThemeData(
      filled: true,
      fillColor: AppColors.muted,
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
        borderSide: BorderSide(color: AppColors.primary, width: 1.5),
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
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.primaryForeground,
        elevation: 0,
        shape: const RoundedRectangleBorder(borderRadius: radius),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.primaryForeground,
        elevation: 0,
        shape: const RoundedRectangleBorder(borderRadius: radius),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.foreground,
        side: const BorderSide(color: AppColors.border),
        shape: const RoundedRectangleBorder(borderRadius: radius),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(foregroundColor: AppColors.primary),
    ),
    dividerTheme: const DividerThemeData(
      color: AppColors.border,
      thickness: 1,
      space: 1,
    ),
    dialogTheme: const DialogThemeData(
      backgroundColor: AppColors.card,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    snackBarTheme: const SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: AppColors.foreground,
      contentTextStyle: TextStyle(color: AppColors.background),
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: AppColors.background,
      indicatorColor: AppColors.primaryForeground,
      labelTextStyle: WidgetStatePropertyAll(
        TextStyle(color: AppColors.foreground),
      ),
    ),
  );
}

ThemeData buildAppDarkTheme() {
  final colorScheme =
      ColorScheme.fromSeed(
        seedColor: AppDarkColors.primary,
        brightness: Brightness.dark,
      ).copyWith(
        primary: AppDarkColors.primary,
        onPrimary: AppDarkColors.primaryForeground,
        primaryContainer: AppDarkColors.secondary,
        onPrimaryContainer: AppDarkColors.primaryForeground,
        secondary: AppDarkColors.secondary,
        onSecondary: AppDarkColors.secondaryForeground,
        secondaryContainer: AppDarkColors.accent,
        onSecondaryContainer: AppDarkColors.accentForeground,
        surface: AppDarkColors.background,
        onSurface: AppDarkColors.foreground,
        outline: AppDarkColors.border,
        outlineVariant: AppDarkColors.border,
        error: AppDarkColors.error,
        onError: AppDarkColors.foreground,
      );
  const radius = BorderRadius.all(Radius.circular(10));

  return ThemeData(
    useMaterial3: true,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: AppDarkColors.background,
    appBarTheme: const AppBarThemeData(
      backgroundColor: AppDarkColors.background,
      foregroundColor: AppDarkColors.foreground,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: const CardThemeData(
      color: AppDarkColors.card,
      elevation: 1,
      shadowColor: Color(0x33000000),
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    inputDecorationTheme: InputDecorationThemeData(
      filled: true,
      fillColor: AppDarkColors.muted,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppDarkColors.border),
      ),
      enabledBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppDarkColors.border),
      ),
      focusedBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppDarkColors.sidebarPrimary, width: 1.5),
      ),
      errorBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppDarkColors.error),
      ),
      focusedErrorBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: AppDarkColors.error, width: 1.5),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppDarkColors.primary,
        foregroundColor: AppDarkColors.primaryForeground,
        elevation: 0,
        shape: const RoundedRectangleBorder(borderRadius: radius),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppDarkColors.primary,
        foregroundColor: AppDarkColors.primaryForeground,
        elevation: 0,
        shape: const RoundedRectangleBorder(borderRadius: radius),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppDarkColors.foreground,
        side: const BorderSide(color: AppDarkColors.border),
        shape: const RoundedRectangleBorder(borderRadius: radius),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(foregroundColor: AppDarkColors.sidebarPrimary),
    ),
    dividerTheme: const DividerThemeData(
      color: AppDarkColors.border,
      thickness: 1,
      space: 1,
    ),
    dialogTheme: const DialogThemeData(
      backgroundColor: AppDarkColors.card,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    snackBarTheme: const SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: AppDarkColors.card,
      contentTextStyle: TextStyle(color: AppDarkColors.foreground),
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: AppDarkColors.background,
      indicatorColor: AppDarkColors.accent,
      labelTextStyle: WidgetStatePropertyAll(
        TextStyle(color: AppDarkColors.foreground),
      ),
    ),
  );
}
