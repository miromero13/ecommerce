import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/shared/widgets/filter_chip.dart';
import 'package:mobile/shared/widgets/product_card.dart';
import 'package:mobile/shared/widgets/product_image.dart';
import 'package:mobile/shared/widgets/product_price.dart';
import 'package:mobile/shared/widgets/quantity_selector.dart';
import 'package:mobile/shared/widgets/variant_selector.dart';

void main() {
  testWidgets('muestra placeholder y carrusel de imágenes', (tester) async {
    await tester.pumpWidget(
      _host(const SizedBox(width: 120, height: 120, child: ProductImage())),
    );

    expect(find.byIcon(Icons.image_outlined), findsOneWidget);

    await tester.pumpWidget(
      _host(
        const SizedBox(
          width: 120,
          height: 120,
          child: ProductImage(
            imageUrl: 'https://example.com/dress.jpg',
            imageUrls: [
              'https://example.com/one.jpg',
              'https://example.com/two.jpg',
            ],
          ),
        ),
      ),
    );

    expect(find.byType(PageView), findsOneWidget);
    expect(find.byType(Image), findsAtLeastNWidgets(1));
  });

  testWidgets('ProductCard acepta una o varias imágenes de variantes', (
    tester,
  ) async {
    await tester.pumpWidget(
      _host(
        SizedBox(
          width: 220,
          child: ProductCard(
            name: 'Vestido',
            price: 149.9,
            imageUrl: 'https://example.com/product.jpg',
            variantImageUrls: const [
              'https://example.com/red.jpg',
              'https://example.com/blue.jpg',
            ],
          ),
        ),
      ),
    );

    expect(find.text('Vestido'), findsOneWidget);
    expect(find.text('Bs 149.90'), findsOneWidget);
    expect(find.byType(ProductPrice), findsOneWidget);
    expect(find.byType(PageView), findsOneWidget);
    expect(find.byType(ProductImage), findsOneWidget);
  });

  testWidgets('QuantitySelector respeta límites', (tester) async {
    var quantity = 1;

    await tester.pumpWidget(
      _host(
        StatefulBuilder(
          builder: (context, setState) => QuantitySelector(
            value: quantity,
            max: 2,
            onChanged: (value) => setState(() => quantity = value),
          ),
        ),
      ),
    );

    expect(find.text('1'), findsOneWidget);
    expect(
      tester
          .widget<IconButton>(find.widgetWithIcon(IconButton, Icons.remove))
          .onPressed,
      isNull,
    );

    await tester.tap(find.byTooltip('Aumentar cantidad'));
    await tester.pump();
    expect(find.text('2'), findsOneWidget);
    expect(
      tester
          .widget<IconButton>(find.widgetWithIcon(IconButton, Icons.add))
          .onPressed,
      isNull,
    );
  });

  testWidgets('selecciona variantes y filtros', (tester) async {
    var selectedVariant = 'small';
    var selectedFilter = false;

    await tester.pumpWidget(
      _host(
        StatefulBuilder(
          builder: (context, setState) => Column(
            children: [
              AppVariantSelector(
                options: const [
                  AppVariantOption(id: 'small', label: 'S'),
                  AppVariantOption(id: 'medium', label: 'M'),
                ],
                selectedId: selectedVariant,
                onChanged: (value) => setState(() => selectedVariant = value),
              ),
              AppFilterChip(
                label: 'En oferta',
                selected: selectedFilter,
                onSelected: (value) => setState(() => selectedFilter = value),
              ),
            ],
          ),
        ),
      ),
    );

    await tester.tap(find.text('M'));
    await tester.tap(find.text('En oferta'));
    expect(selectedVariant, 'medium');
    expect(selectedFilter, isTrue);
  });
}

Widget _host(Widget child) {
  return MaterialApp(
    theme: buildAppTheme(),
    home: Scaffold(body: child),
  );
}
