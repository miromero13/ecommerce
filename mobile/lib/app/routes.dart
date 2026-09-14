import 'package:flutter/material.dart';

import '../features/auth/auth_controller.dart';
import '../features/auth/login_page.dart';
import '../features/catalog/catalog_controller.dart';
import '../features/catalog/catalog_page.dart';
import '../features/catalog/product_detail_page.dart';
import '../features/cart/cart_page.dart';
import '../shared/widgets/app_scaffold.dart';
import '../features/profile/profile_page.dart';
import '../features/reservations/reservation_models.dart';
import '../features/reservations/reservations_page.dart';
import '../features/orders/orders_page.dart';

abstract final class AppRoutes {
  static const catalog = '/';
  static const cart = '/cart';
  static const account = '/account';
  static const reservations = '/reservations';
  static const orders = '/orders';
  static const productDetail = '/product';
  static const login = '/login';
}

abstract final class AppRouter {
  static Route<dynamic> onGenerateRoute(
    RouteSettings settings, {
    required AuthController authController,
    CatalogController? catalogController,
  }) {
    return switch (settings.name) {
      AppRoutes.catalog => _page(
        settings,
        CatalogPage(controller: catalogController),
        selectedIndex: 0,
      ),
      AppRoutes.cart => _page(
        settings,
        CartPage(authController: authController),
        selectedIndex: 1,
      ),
      AppRoutes.account => _page(
        settings,
        ProfilePage(authController: authController),
        selectedIndex: 2,
      ),
      AppRoutes.reservations => _page(
        settings,
        ReservationsPage(
          authController: authController,
          arguments: settings.arguments is ReservationArguments
              ? settings.arguments as ReservationArguments
              : null,
        ),
        selectedIndex: 2,
      ),
      AppRoutes.orders => _page(
        settings,
        OrdersPage(authController: authController),
        selectedIndex: 2,
      ),
      AppRoutes.productDetail => _page(
        settings,
        ProductDetailPage(
          arguments: settings.arguments is ProductDetailArguments
              ? settings.arguments as ProductDetailArguments
              : null,
          authController: authController,
        ),
      ),
      AppRoutes.login => _page(
        settings,
        _LoginRoutePage(authController: authController),
      ),
      _ => _page(settings, CatalogPage(controller: catalogController)),
    };
  }

  static Route<dynamic> _page(
    RouteSettings settings,
    Widget page, {
    int? selectedIndex,
  }) {
    final child = selectedIndex == null
        ? page
        : _ShellPage(index: selectedIndex, child: page);
    return MaterialPageRoute<void>(settings: settings, builder: (_) => child);
  }
}

class _ShellPage extends StatelessWidget {
  const _ShellPage({required this.index, required this.child});

  final int index;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: switch (index) {
        0 => 'Catálogo',
        1 => 'Carrito',
        _ => 'Cuenta',
      },
      selectedIndex: index,
      onDestinationSelected: (nextIndex) {
        final route = switch (nextIndex) {
          0 => AppRoutes.catalog,
          1 => AppRoutes.cart,
          _ => AppRoutes.account,
        };
        Navigator.of(context).pushReplacementNamed(route);
      },
      body: child,
    );
  }
}

class _LoginRoutePage extends StatelessWidget {
  const _LoginRoutePage({required this.authController});

  final AuthController authController;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Iniciar sesión')),
      body: LoginPage(
        controller: authController,
        showGuestButton: true,
        onGuest: () => Navigator.of(context).pop(),
      ),
    );
  }
}
