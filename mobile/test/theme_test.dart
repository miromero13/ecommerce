import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme.dart';

void main() {
  group('AppColors (:root light tokens)', () {
    test('contiene todos los tokens definidos en la paleta CSS', () {
      expect(AppColors.background, const Color(0xFFFFFFFF));
      expect(AppColors.foreground, const Color(0xFF1C2124));
      expect(AppColors.card, const Color(0xFFFFFFFF));
      expect(AppColors.cardForeground, const Color(0xFF1C2124));
      expect(AppColors.popover, const Color(0xFFFFFFFF));
      expect(AppColors.popoverForeground, const Color(0xFF1C2124));
      expect(AppColors.primary, const Color(0xFF007F82));
      expect(AppColors.primaryForeground, const Color(0xFFEBFDFB));
      expect(AppColors.secondary, const Color(0xFFF6F5F6));
      expect(AppColors.secondaryForeground, const Color(0xFF2D2C2E));
      expect(AppColors.muted, const Color(0xFFF3F5F5));
      expect(AppColors.mutedForeground, const Color(0xFF6E7D82));
      expect(AppColors.accent, const Color(0xFFF3F5F5));
      expect(AppColors.accentForeground, const Color(0xFF2D3437));
      expect(AppColors.destructive, const Color(0xFFE12739));
      expect(AppColors.border, const Color(0xFFE6EBEC));
      expect(AppColors.input, const Color(0xFFE6EBEC));
      expect(AppColors.ring, const Color(0xFF9CAAB0));
      expect(AppColors.chart1, const Color(0xFF64E3D4));
      expect(AppColors.chart2, const Color(0xFF24B9B4));
      expect(AppColors.chart3, const Color(0xFF009D9E));
      expect(AppColors.chart4, const Color(0xFF007F82));
      expect(AppColors.chart5, const Color(0xFF00666A));
      expect(AppColors.sidebar, const Color(0xFFFAFBFB));
      expect(AppColors.sidebarForeground, const Color(0xFF1C2124));
      expect(AppColors.sidebarPrimary, const Color(0xFF009D9E));
      expect(AppColors.sidebarPrimaryForeground, const Color(0xFFEBFDFB));
      expect(AppColors.sidebarAccent, const Color(0xFFF3F5F5));
      expect(AppColors.sidebarAccentForeground, const Color(0xFF2D3437));
      expect(AppColors.sidebarBorder, const Color(0xFFE6EBEC));
      expect(AppColors.sidebarRing, const Color(0xFF9CAAB0));
    });
  });

  group('AppDarkColors (.dark tokens)', () {
    test('contiene todos los tokens definidos en la paleta oscura', () {
      expect(AppDarkColors.background, const Color(0xFF1C2124));
      expect(AppDarkColors.foreground, const Color(0xFFFAFBFB));
      expect(AppDarkColors.card, const Color(0xFF2D3437));
      expect(AppDarkColors.cardForeground, const Color(0xFFFAFBFB));
      expect(AppDarkColors.popover, const Color(0xFF2D3437));
      expect(AppDarkColors.popoverForeground, const Color(0xFFFAFBFB));
      expect(AppDarkColors.primary, const Color(0xFF00666A));
      expect(AppDarkColors.primaryForeground, const Color(0xFFEBFDFB));
      expect(AppDarkColors.secondary, const Color(0xFF3B3A3C));
      expect(AppDarkColors.secondaryForeground, const Color(0xFFFAFAFA));
      expect(AppDarkColors.muted, const Color(0xFF3A4245));
      expect(AppDarkColors.mutedForeground, const Color(0xFF9CAAB0));
      expect(AppDarkColors.accent, const Color(0xFF3A4245));
      expect(AppDarkColors.accentForeground, const Color(0xFFFAFBFB));
      expect(AppDarkColors.destructive, const Color(0xFFFF6060));
      expect(AppDarkColors.border, const Color(0x1AFFFFFF));
      expect(AppDarkColors.input, const Color(0x26FFFFFF));
      expect(AppDarkColors.ring, const Color(0xFF6E7D82));
      expect(AppDarkColors.chart1, const Color(0xFF64E3D4));
      expect(AppDarkColors.chart2, const Color(0xFF24B9B4));
      expect(AppDarkColors.chart3, const Color(0xFF009D9E));
      expect(AppDarkColors.chart4, const Color(0xFF007F82));
      expect(AppDarkColors.chart5, const Color(0xFF00666A));
      expect(AppDarkColors.sidebar, const Color(0xFF2D3437));
      expect(AppDarkColors.sidebarForeground, const Color(0xFFFAFBFB));
      expect(AppDarkColors.sidebarPrimary, const Color(0xFF24B9B4));
      expect(AppDarkColors.sidebarPrimaryForeground, const Color(0xFF193F40));
      expect(AppDarkColors.sidebarAccent, const Color(0xFF3A4245));
      expect(AppDarkColors.sidebarAccentForeground, const Color(0xFFFAFBFB));
      expect(AppDarkColors.sidebarBorder, const Color(0x1AFFFFFF));
      expect(AppDarkColors.sidebarRing, const Color(0xFF6E7D82));
    });
  });

  group('buildAppTheme y buildAppDarkTheme', () {
    test('construye tema claro con los colores esperados', () {
      final theme = buildAppTheme();
      expect(theme.brightness, Brightness.light);
      expect(theme.colorScheme.primary, AppColors.primary);
      expect(theme.colorScheme.onPrimary, AppColors.primaryForeground);
      expect(theme.colorScheme.surface, AppColors.background);
      expect(theme.scaffoldBackgroundColor, AppColors.background);
      expect(theme.cardTheme.color, AppColors.card);
    });

    test('construye tema oscuro con los colores esperados', () {
      final darkTheme = buildAppDarkTheme();
      expect(darkTheme.brightness, Brightness.dark);
      expect(darkTheme.colorScheme.primary, AppDarkColors.primary);
      expect(darkTheme.colorScheme.onPrimary, AppDarkColors.primaryForeground);
      expect(darkTheme.colorScheme.surface, AppDarkColors.background);
      expect(darkTheme.scaffoldBackgroundColor, AppDarkColors.background);
      expect(darkTheme.cardTheme.color, AppDarkColors.card);
    });
  });
}
