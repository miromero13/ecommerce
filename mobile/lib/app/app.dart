import 'dart:async';

import 'package:flutter/material.dart';

import '../features/auth/auth_controller.dart';
import '../features/auth/login_page.dart';
import '../features/auth/splash_page.dart';
import '../features/catalog/catalog_controller.dart';
import '../features/catalog/catalog_page.dart';
import '../features/notifications/notification_controller.dart';
import '../features/notifications/notification_push_service.dart';
import '../shared/widgets/app_scaffold.dart';
import 'routes.dart';
import 'theme.dart';

class MobileApp extends StatefulWidget {
  const MobileApp({
    super.key,
    this.authController,
    this.catalogController,
    this.notificationController,
    this.pushService,
  });

  final AuthController? authController;
  final CatalogController? catalogController;
  final NotificationController? notificationController;
  final NotificationPushService? pushService;

  @override
  State<MobileApp> createState() => _MobileAppState();
}

class _MobileAppState extends State<MobileApp> {
  late final AuthController _authController;
  late final bool _ownsController;
  late final NotificationController _notificationController;
  late final bool _ownsNotificationController;
  late final NotificationPushService _pushService;
  final _navigatorKey = GlobalKey<NavigatorState>();

  @override
  void initState() {
    super.initState();
    _ownsController = widget.authController == null;
    _authController = widget.authController ?? AuthController();
    _ownsNotificationController = widget.notificationController == null;
    _notificationController =
        widget.notificationController ??
        NotificationController(authController: _authController);
    _pushService = widget.pushService ?? NotificationPushService();
    _authController.addListener(_handleAuthChanged);
    _authController.restoreSession();
  }

  @override
  void dispose() {
    _authController.removeListener(_handleAuthChanged);
    unawaited(_pushService.stop());
    if (_ownsNotificationController) _notificationController.dispose();
    if (_ownsController) {
      _authController.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FashionStore',
      navigatorKey: _navigatorKey,
      theme: buildAppTheme(),
      home: _AuthGate(
        authController: _authController,
        catalogController: widget.catalogController,
      ),
      onGenerateRoute: (settings) => AppRouter.onGenerateRoute(
        settings,
        authController: _authController,
        catalogController: widget.catalogController,
        notificationController: _notificationController,
      ),
    );
  }

  void _handleAuthChanged() {
    if (!_authController.isAuthenticated) {
      unawaited(_pushService.stop());
      return;
    }
    unawaited(_notificationController.load());
    unawaited(
      _pushService.start(
        onToken: _notificationController.registerToken,
        onForegroundMessage: () => unawaited(_notificationController.load()),
        onTap: _openNotification,
      ),
    );
  }

  void _openNotification(Map<String, String> data) {
    final navigator = _navigatorKey.currentState;
    if (navigator == null) return;
    final destination = data['destination'];
    final id = destination == 'orders'
        ? data['order_id']
        : destination == 'reservations'
        ? data['reservation_id']
        : null;
    if (destination == 'orders' && id != null && id.isNotEmpty) {
      navigator.pushNamed(AppRoutes.orders, arguments: id);
    } else if (destination == 'reservations' && id != null && id.isNotEmpty) {
      navigator.pushNamed(AppRoutes.reservations, arguments: id);
    } else {
      navigator.pushNamed(AppRoutes.notifications);
    }
  }
}

class _AuthGate extends StatelessWidget {
  const _AuthGate({
    required this.authController,
    this.catalogController,
  });

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
