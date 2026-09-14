import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/features/catalog/catalog_models.dart';
import 'package:mobile/features/catalog/product_detail_page.dart';

void main() {
  testWidgets(
    'muestra el producto y cambia toda la información al seleccionar variante',
    (tester) async {
      final product = Product(
        id: 'product-id',
        name: 'Blusa Demo',
        description: 'Descripción de prueba',
        price: 110,
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
}
