import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/features/catalog/catalog_api.dart';

void main() {
  test('consume el catálogo y sus filtros públicos reales', () async {
    final api = CatalogApi(client: ApiClient());

    final products = await api.getProducts();
    final categories = await api.getCategories();
    final sizes = await api.getSizes();
    final colors = await api.getColors();
    final seasons = await api.getSeasons();
    final collections = await api.getCollections();
    final branches = await api.getBranches();

    expect(products, isNotEmpty);
    expect(products.first.variants, isNotEmpty);
    expect(categories, isNotEmpty);
    expect(sizes, isNotEmpty);
    expect(colors, isNotEmpty);
    expect(seasons, isNotEmpty);
    expect(collections, isNotEmpty);
    expect(branches, isNotEmpty);
  });

  test('envía los filtros públicos de productos', () async {
    final products = await CatalogApi(client: ApiClient()).getProducts(
      query: 'blusa',
      branchId: 'ca37167f-0b87-4c2b-8cba-40daacbcb295',
      categoryId: '619beed1-178a-4664-9223-bf4f45435181',
      sizeId: '626d6e7c-73de-4a2d-837f-5005d447ad28',
      colorId: '2110bdc8-7834-4260-86cf-739e12533891',
      seasonId: '2af816e8-acdf-40ef-8fd1-5c21683535b1',
      collectionId: 'afa8fc49-8bc9-4f9c-a1e1-4cb5e4c96146',
    );

    expect(products, isA<List<dynamic>>());
  });
}
