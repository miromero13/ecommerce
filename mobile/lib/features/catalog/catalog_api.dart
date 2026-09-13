import '../../core/network/api_client.dart';
import 'catalog_models.dart';

class CatalogApi {
  CatalogApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<List<Product>> getProducts({
    String? query,
    String? branchId,
    String? categoryId,
    String? sizeId,
    String? colorId,
    String? seasonId,
    String? collectionId,
  }) {
    final queryParameters = <String, dynamic>{};
    final trimmedQuery = query?.trim();
    if (trimmedQuery != null && trimmedQuery.isNotEmpty) {
      queryParameters['q'] = trimmedQuery;
    }
    if (branchId != null) queryParameters['branch_id'] = branchId;
    if (categoryId != null) queryParameters['category_id'] = categoryId;
    if (sizeId != null) queryParameters['size_id'] = sizeId;
    if (colorId != null) queryParameters['color_id'] = colorId;
    if (seasonId != null) queryParameters['season_id'] = seasonId;
    if (collectionId != null) queryParameters['collection_id'] = collectionId;

    return _getList(
      'catalog/products',
      queryParameters: queryParameters,
      parser: Product.fromJson,
    );
  }

  Future<List<Category>> getCategories() {
    return _getList('catalog/categories', parser: Category.fromJson);
  }

  Future<List<Size>> getSizes() {
    return _getList('catalog/sizes', parser: Size.fromJson);
  }

  Future<List<CatalogColor>> getColors() {
    return _getList('catalog/colors', parser: CatalogColor.fromJson);
  }

  Future<List<Season>> getSeasons() {
    return _getList('catalog/seasons', parser: Season.fromJson);
  }

  Future<List<Collection>> getCollections() {
    return _getList('catalog/collections', parser: Collection.fromJson);
  }

  Future<List<Branch>> getBranches() {
    return _getList('branches/public', parser: Branch.fromJson);
  }

  Future<List<T>> _getList<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    required T Function(Map<String, dynamic>) parser,
  }) async {
    final response = await _client.get<List<T>>(
      path,
      queryParameters: queryParameters,
      parser: (value) => _parseList(value, parser),
    );
    return response.data ?? const [];
  }

  static List<T> _parseList<T>(
    dynamic value,
    T Function(Map<String, dynamic>) parser,
  ) {
    if (value is! List) {
      throw const FormatException('La respuesta del catálogo no es una lista');
    }
    return value
        .map((item) {
          if (item is! Map) {
            throw const FormatException('Un elemento del catálogo es inválido');
          }
          return parser(Map<String, dynamic>.from(item));
        })
        .toList(growable: false);
  }
}
