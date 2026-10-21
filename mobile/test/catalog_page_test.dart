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
  testWidgets('muestra accesos visibles para carrito y reservas', (
    tester,
  ) async {
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
    await tester.pumpAndSettle();
    expect(find.text('Prenda agregada a la reserva.'), findsOneWidget);

    await tester.tap(find.widgetWithText(OutlinedButton, 'Reservas'));
    await tester.pumpAndSettle();

    expect(routeName, AppRoutes.reservationCreate);
    expect(creationArguments!.items, hasLength(2));
    expect(creationArguments!.items.last.variantId, 'variant-2');
    expect(creationArguments!.items.last.quantity, 2);
  });

  testWidgets('abre el bottom sheet de filtros desde abajo y permite cerrarlo', (
    tester,
  ) async {
    final controller = CatalogController()..status = CatalogStatus.ready;
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(body: CatalogPage(controller: controller)),
      ),
    );

    // Encuentra el botón para abrir filtros
    final filterButtonFinder = find.byIcon(Icons.tune_rounded);
    expect(filterButtonFinder, findsOneWidget);
    await tester.tap(filterButtonFinder);
    await tester.pumpAndSettle();

    // Verifica que el bottom sheet está visible con su título y opciones
    expect(find.text('Filtros'), findsNWidgets(2));
    expect(find.text('Categoría'), findsOneWidget);
    expect(find.text('Talla'), findsOneWidget);
    expect(find.text('Sucursal física'), findsNothing);

    // Cierra el bottom sheet
    await tester.tap(find.byTooltip('Cerrar'));
    await tester.pumpAndSettle();

    // Ya no debe mostrarse el modal
    expect(find.text('Filtros'), findsOneWidget);
    expect(find.text('Categoría'), findsNothing);
  });

  testWidgets('selecciona y deselecciona chips de filtros en el bottom sheet', (
    tester,
  ) async {
    final controller = CatalogController()
      ..status = CatalogStatus.ready
      ..categories = const [Category(id: 'cat-1', name: 'Vestidos')]
      ..sizes = const [Size(id: 'sz-1', name: 'M')]
      ..colors = const [CatalogColor(id: 'col-1', name: 'Rojo', hexCode: '#FF0000')];
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(body: CatalogPage(controller: controller)),
      ),
    );

    // Abrir bottom sheet
    await tester.tap(find.byIcon(Icons.tune_rounded));
    await tester.pumpAndSettle();

    // Seleccionar la categoría 'Vestidos'
    expect(find.text('Vestidos'), findsOneWidget);
    await tester.tap(find.text('Vestidos'));
    await tester.pumpAndSettle();
    expect(controller.categoryId, 'cat-1');

    // Seleccionar la talla 'M'
    expect(find.text('M'), findsOneWidget);
    await tester.tap(find.text('M'));
    await tester.pumpAndSettle();
    expect(controller.sizeId, 'sz-1');

    // Deseleccionar categoría pulsando 'Todas'
    final todasCategory = find.widgetWithText(ChoiceChip, 'Todas').first;
    await tester.tap(todasCategory);
    await tester.pumpAndSettle();
    expect(controller.categoryId, isNull);
  });

  testWidgets('lista las sucursales al seleccionar una marca con scroll y badge', (
    tester,
  ) async {
    final controller = CatalogController()
      ..status = CatalogStatus.ready
      ..tenants = const [Tenant(id: 't-1', name: 'Zara', slug: 'zara')]
      ..branches = const [
        Branch(id: 'b-1', tenantId: 't-1', name: 'Central', city: 'La Paz', isDefault: true, isActive: true),
        Branch(id: 'b-2', tenantId: 't-1', name: 'Sur', city: 'Santa Cruz', isDefault: false, isActive: true),
      ];
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Scaffold(body: CatalogPage(controller: controller)),
      ),
    );

    // Inicialmente no hay marca seleccionada, por lo que no se muestran sucursales
    expect(find.text('Sucursales'), findsNothing);

    // Seleccionar la tienda 'Zara'
    await tester.tap(find.text('Zara'));
    await tester.pumpAndSettle();

    // Ahora se lista la fila de sucursales con su badge
    expect(find.text('Sucursales'), findsOneWidget);
    expect(find.text('2'), findsOneWidget);
    expect(find.text('Todas las sucursales'), findsOneWidget);
    expect(find.text('Central (La Paz)'), findsOneWidget);
    expect(find.text('Sur (Santa Cruz)'), findsOneWidget);

    // Seleccionar la sucursal 'Central (La Paz)'
    await tester.tap(find.text('Central (La Paz)'));
    await tester.pumpAndSettle();
    expect(controller.branchId, 'b-1');

    // Deseleccionar pulsando 'Todas las sucursales'
    await tester.tap(find.text('Todas las sucursales'));
    await tester.pumpAndSettle();
    expect(controller.branchId, isNull);
  });
}
