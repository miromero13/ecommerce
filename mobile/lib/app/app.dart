import 'package:flutter/material.dart';

import '../features/auth/auth_controller.dart';
import '../features/auth/login_page.dart';
import '../features/auth/splash_page.dart';
import '../features/catalog/catalog_controller.dart';
import '../features/catalog/catalog_page.dart';
import '../shared/widgets/app_scaffold.dart';
import 'routes.dart';
import 'theme.dart';

class MobileApp extends StatefulWidget {
  const MobileApp({super.key, this.authController, this.catalogController});

  final AuthController? authController;
  final CatalogController? catalogController;

  @override
  State<MobileApp> createState() => _MobileAppState();
}

class _MobileAppState extends State<MobileApp> {
  late final AuthController _authController;
  late final bool _ownsController;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.authController == null;
    _authController = widget.authController ?? AuthController();
    _authController.restoreSession();
  }

  @override
  void dispose() {
    if (_ownsController) {
      _authController.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FashionStore',
      theme: buildAppTheme(),
      home: _AuthGate(
        authController: _authController,
        catalogController: widget.catalogController,
      ),
      onGenerateRoute: (settings) => AppRouter.onGenerateRoute(
        settings,
        authController: _authController,
        catalogController: widget.catalogController,
      ),
    );
  }
}

class _AuthGate extends StatelessWidget {
  const _AuthGate({required this.authController, this.catalogController});

  final AuthController authController;
  final CatalogController? catalogController;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: authController,
      builder: (context, _) {
        if (authController.status == AuthStatus.loading) {
          return const SplashPage();
        }
        if (authController.isAuthenticated || authController.hasGuestAccess) {
          return _MainPage(
            authController: authController,
            catalogController: catalogController,
          );
        }
        return Scaffold(
          body: SafeArea(
            child: LoginPage(
              controller: authController,
              showCloseButton: false,
              showGuestButton: true,
              centerContent: true,
            ),
          ),
        );
      },
    );
  }
}

class _MainPage extends StatelessWidget {
  const _MainPage({required this.authController, this.catalogController});

  final AuthController authController;
  final CatalogController? catalogController;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'Catálogo',
      selectedIndex: 0,
      onDestinationSelected: (index) {
        final route = switch (index) {
          0 => AppRoutes.catalog,
          1 => AppRoutes.management,
          _ => AppRoutes.account,
        };
        Navigator.of(context).pushReplacementNamed(route);
      },
      body: CatalogPage(
        controller: catalogController,
        authController: authController,
      ),
    );
  }
}
