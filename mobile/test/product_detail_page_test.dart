import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/features/auth/auth_controller.dart';
import 'package:mobile/features/catalog/catalog_models.dart';
import 'package:mobile/features/catalog/product_detail_page.dart';
import 'package:mobile/features/reservations/reservation_models.dart';

void main() {
  testWidgets(
    'muestra el producto y cambia toda la información al seleccionar variante',
    (tester) async {
      final product = Product(
        id: 'product-id',
        name: 'Blusa Demo',
        description: 'Descripción de prueba',
        categoryId: 'category-id',
        variants: [
          ProductVariant(
            id: 'variant-1',
            productId: 'product-id',
            sku: 'SKU-1',
            price: 110,
            sizeId: 'size-s',
            colorId: 'color-black',
            status: ProductStatus.active,
            branchQuantity: 0,
          ),
          ProductVariant(
            id: 'variant-2',
            productId: 'product-id',
            sku: 'SKU-2',
            price: 125,
            sizeId: 'size-m',
            colorId: 'color-red',
            status: ProductStatus.active,
            branchQuantity: 4,
          ),
        ],
      );

      await tester.pumpWidget(
        MaterialApp(
          theme: buildAppTheme(),
          home: ProductDetailPage(
            arguments: ProductDetailArguments(
              product: product,
              sizes: const [
                Size(id: 'size-s', name: 'S'),
                Size(id: 'size-m', name: 'M'),
              ],
              colors: const [
                CatalogColor(id: 'color-black', name: 'Negro'),
                CatalogColor(id: 'color-red', name: 'Rojo'),
              ],
              branches: const [
                Branch(
                  id: 'branch-id',
                  name: 'Sucursal Central',
                  city: 'La Paz',
                  isDefault: true,
                  isActive: true,
                ),
              ],
              branchId: 'branch-id',
            ),
          ),
        ),
      );

      await tester.drag(find.byType(ListView).first, const Offset(0, -700));
      await tester.pump();
      expect(find.text('Blusa Demo'), findsOneWidget);
      expect(find.text('Descripción de prueba'), findsOneWidget);
      expect(find.text('SKU-1'), findsOneWidget);
      expect(find.text('Agotado en Sucursal Central'), findsOneWidget);

      await tester.tap(find.text('M · Rojo · SKU-2'));
      await tester.pump();

      expect(find.text('Disponible (4) en Sucursal Central'), findsOneWidget);
      expect(find.text('Bs 125.00'), findsOneWidget);
    },
  );

  testWidgets('mantiene la ruta pública aunque no reciba producto', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(theme: buildAppTheme(), home: const ProductDetailPage()),
    );

    expect(
      find.text('El detalle reutilizará el producto del catálogo.'),
      findsOneWidget,
    );
  });

  testWidgets('devuelve el borrador con la variante y cantidad seleccionadas', (
    tester,
  ) async {
    final authController = AuthController();
    addTearDown(authController.dispose);
    ReservationArguments? returnedArguments;
    const product = Product(
      id: 'product-id',
      name: 'Blusa Demo',
      categoryId: 'category-id',
      imageUrl: 'product-image',
      variants: [
        ProductVariant(
          id: 'variant-1',
          productId: 'product-id',
          sku: 'SKU-1',
          price: 110,
          status: ProductStatus.active,
          branchQuantity: 0,
        ),
        ProductVariant(
          id: 'variant-2',
          productId: 'product-id',
          sku: 'SKU-2',
          price: 125,
          status: ProductStatus.active,
          branchQuantity: 4,
          imageUrl: 'variant-image',
        ),
      ],
    );

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                returnedArguments = await Navigator.of(context)
                    .push<ReservationArguments>(
                      MaterialPageRoute(
                        builder: (_) => ProductDetailPage(
                          arguments: const ProductDetailArguments(
                            product: product,
                            sizes: [Size(id: 'size-m', name: 'M')],
                            colors: [
                              CatalogColor(id: 'color-red', name: 'Rojo'),
                            ],
                            reservationArguments: ReservationArguments(
                              items: [
                                ReservationDraftItem(
                                  variantId: 'variant-1',
                                  quantity: 1,
                                  productName: 'Otra blusa',
                                  variantSku: 'SKU-1',
                                ),
                                ReservationDraftItem(
                                  variantId: 'variant-2',
                                  quantity: 2,
                                  productName: 'Blusa Demo',
                                  variantSku: 'SKU-2',
                                ),
                              ],
                            ),
                          ),
                          authController: authController,
                        ),
                      ),
                    );
              },
              child: const Text('Abrir detalle'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Abrir detalle'));
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView).first, const Offset(0, -700));
    await tester.pump();
    await tester.tap(find.text('M · Rojo · SKU-2'));
    await tester.tap(find.byTooltip('Aumentar cantidad'));
    await tester.tap(find.widgetWithText(OutlinedButton, 'Reservar prenda'));
    await tester.pumpAndSettle();

    final items = returnedArguments!.items;
    expect(items, hasLength(2));
    expect(items.first.variantId, 'variant-1');
    expect(items.first.quantity, 1);
    expect(items.last.variantId, 'variant-2');
    expect(items.last.quantity, 4);
    expect(items.last.productName, 'Blusa Demo');
    expect(items.last.variantSku, 'SKU-2');
    expect(items.last.imageUrl, 'variant-image');
  });

  testWidgets('muestra probar prenda solo cuando hay una imagen', (
    tester,
  ) async {
    ProductDetailArguments arguments(Product product) =>
        ProductDetailArguments(product: product);

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: ProductDetailPage(
          arguments: arguments(
            const Product(
              id: 'without-image',
              name: 'Sin imagen',
              categoryId: 'category-id',
            ),
          ),
        ),
      ),
    );
    expect(find.text('Probar prenda'), findsNothing);

    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(),
        home: ProductDetailPage(
          arguments: arguments(
            const Product(
              id: 'with-image',
              name: 'Con imagen',
              categoryId: 'category-id',
              imageUrl: 'https://example.com/garment.jpg',
            ),
          ),
        ),
      ),
    );
    await tester.scrollUntilVisible(
      find.text('Probar prenda'),
      500,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Probar prenda'), findsOneWidget);
  });
}
