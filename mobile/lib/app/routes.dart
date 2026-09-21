import 'package:flutter/material.dart';

import '../features/auth/auth_controller.dart';
import '../features/auth/login_page.dart';
import '../features/catalog/catalog_controller.dart';
import '../features/catalog/catalog_page.dart';
import '../features/catalog/product_detail_page.dart';
import '../features/cart/cart_page.dart';
import '../features/management/management_page.dart';
import '../features/orders/checkout_page.dart';
import '../features/orders/orders_page.dart';
import '../features/profile/profile_page.dart';
import '../features/reservations/reservation_create_page.dart';
import '../features/reservations/reservation_models.dart';
import '../features/reservations/reservations_page.dart';
import '../shared/widgets/app_scaffold.dart';

abstract final class AppRoutes {
  static const catalog = '/';
  static const cart = '/cart';
  static const management = '/management';
  static const account = '/account';
  static const reservations = '/reservations';
  static const reservationCreate = '/reservation-create';
  static const orders = '/orders';
  static const checkout = '/checkout';
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
        CatalogPage(
          controller: catalogController,
          authController: authController,
          reservationArguments: settings.arguments is ReservationArguments
              ? settings.arguments as ReservationArguments
              : null,
        ),
        selectedIndex: 0,
      ),
      AppRoutes.cart => _page(
        settings,
        CartPage(authController: authController),
        selectedIndex: 0,
        shellTitle: 'Carrito',
      ),
      AppRoutes.management => _page(
        settings,
        const ManagementPage(),
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
          initialReservationId: settings.arguments is String
              ? settings.arguments as String
              : null,
        ),
        selectedIndex: 1,
      ),
      AppRoutes.orders => _page(
        settings,
        OrdersPage(
          authController: authController,
          initialOrderId: settings.arguments is String
              ? settings.arguments as String
              : null,
        ),
        selectedIndex: 1,
      ),
      AppRoutes.reservationCreate => _page(
        settings,
        ReservationCreatePage(
          authController: authController,
          arguments: settings.arguments is ReservationArguments
              ? settings.arguments as ReservationArguments
              : null,
        ),
      ),
      AppRoutes.checkout => _page(
        settings,
        CheckoutPage(
          authController: authController,
          orderId: settings.arguments is String
              ? settings.arguments as String
              : null,
        ),
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
      _ => _page(
        settings,
        CatalogPage(
          controller: catalogController,
          authController: authController,
        ),
      ),
    };
  }

  static Route<dynamic> _page(
    RouteSettings settings,
    Widget page, {
    int? selectedIndex,
    String? shellTitle,
  }) {
    final child = selectedIndex == null
        ? page
        : _ShellPage(index: selectedIndex, title: shellTitle, child: page);
    return MaterialPageRoute<void>(settings: settings, builder: (_) => child);
  }
}

class _ShellPage extends StatelessWidget {
  const _ShellPage({required this.index, this.title, required this.child});

  final int index;
  final String? title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title:
          title ??
          switch (index) {
            0 => 'Catálogo',
            1 => 'Gestiones',
            _ => 'Cuenta',
          },
      selectedIndex: index,
      onDestinationSelected: (nextIndex) {
        final route = switch (nextIndex) {
          0 => AppRoutes.catalog,
          1 => AppRoutes.management,
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
