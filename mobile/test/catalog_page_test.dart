import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/routes.dart';
import 'package:mobile/app/theme.dart';
import 'package:mobile/features/catalog/catalog_controller.dart';
import 'package:mobile/features/catalog/catalog_models.dart';
import 'package:mobile/features/catalog/catalog_page.dart';
import 'package:mobile/features/catalog/product_detail_page.dart';
import 'package:mobile/features/reservations/reservation_models.dart';

void main() {
  testWidgets('muestra accesos visibles para carrito y reservas', (tester) async {
    final controller = CatalogController()..status = CatalogStatus.ready;
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(body: CatalogPage(controller: controller)),
      ),
    );

    expect(find.widgetWithText(FilledButton, 'Carrito'), findsOneWidget);
    expect(find.widgetWithText(OutlinedButton, 'Reservas'), findsOneWidget);
  });

  testWidgets('abre la creación de reservas desde el acceso del catálogo', (
    tester,
  ) async {
    final controller = CatalogController()..status = CatalogStatus.ready;
    addTearDown(controller.dispose);
    String? routeName;
    ReservationArguments? arguments;

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(body: CatalogPage(controller: controller)),
        onGenerateRoute: (settings) {
          routeName = settings.name;
          arguments = settings.arguments as ReservationArguments;
          return MaterialPageRoute<void>(
            builder: (_) => const SizedBox.shrink(),
          );
        },
      ),
    );

    await tester.tap(find.widgetWithText(OutlinedButton, 'Reservas'));
    await tester.pumpAndSettle();

    expect(routeName, AppRoutes.reservationCreate);
    expect(arguments!.items, isEmpty);
  });

  testWidgets('acumula el borrador al volver del detalle y abre la creación', (
    tester,
  ) async {
    final controller = CatalogController()
      ..status = CatalogStatus.ready
      ..products = const [
        Product(
          id: 'product-id',
          name: 'Blusa demo',
          categoryId: 'category-id',
          variants: [
            ProductVariant(
              id: 'variant-2',
              productId: 'product-id',
              sku: 'SKU-2',
              price: 100,
              status: ProductStatus.active,
            ),
          ],
        ),
      ];
    addTearDown(controller.dispose);
    const initialArguments = ReservationArguments(
      items: [
        ReservationDraftItem(
          variantId: 'variant-1',
          quantity: 1,
          productName: 'Pantalón demo',
        ),
      ],
    );
    String? routeName;
    ReservationArguments? creationArguments;
    ProductDetailArguments? detailArguments;

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(
          body: CatalogPage(
            controller: controller,
            reservationArguments: initialArguments,
          ),
        ),
        onGenerateRoute: (settings) {
          routeName = settings.name;
          if (settings.name == AppRoutes.productDetail) {
            detailArguments = settings.arguments as ProductDetailArguments;
            return MaterialPageRoute<ReservationArguments>(
              builder: (context) => Scaffold(
                body: TextButton(
                  onPressed: () => Navigator.of(context).pop(
                    ReservationArguments(
                      items: [
                        ...detailArguments!.reservationArguments!.items,
                        const ReservationDraftItem(
                          variantId: 'variant-2',
                          quantity: 2,
                          productName: 'Blusa demo',
                        ),
                      ],
                    ),
                  ),
                  child: const Text('Agregar desde detalle'),
                ),
              ),
            );
          }
          if (settings.name == AppRoutes.reservationCreate) {
            creationArguments = settings.arguments as ReservationArguments;
          }
          return MaterialPageRoute<void>(
            builder: (_) => const SizedBox.shrink(),
          );
        },
      ),
    );

    await tester.tap(find.text('Blusa demo'));
    await tester.pumpAndSettle();
    expect(
      detailArguments!.reservationArguments!.items.single.variantId,
      'variant-1',
    );

    await tester.tap(find.text('Agregar desde detalle'));
    await tester.pump();
    expect(find.text('Prenda agregada a la reserva.'), findsOneWidget);

    await tester.tap(find.widgetWithText(OutlinedButton, 'Reservas'));
    await tester.pumpAndSettle();

    expect(routeName, AppRoutes.reservationCreate);
    expect(creationArguments!.items, hasLength(2));
    expect(creationArguments!.items.last.variantId, 'variant-2');
    expect(creationArguments!.items.last.quantity, 2);
  });
}
