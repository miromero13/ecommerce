import 'package:flutter/foundation.dart' show ChangeNotifier;

import '../../core/network/api_exception.dart';
import 'catalog_api.dart';
import 'catalog_models.dart';

enum CatalogStatus { idle, loading, ready, error }

class CatalogController extends ChangeNotifier {
  CatalogController({CatalogApi? api}) : _api = api ?? CatalogApi();

  final CatalogApi _api;

  CatalogStatus status = CatalogStatus.idle;
  String? errorMessage;
  List<Product> products = const [];
  List<Category> categories = const [];
  List<Size> sizes = const [];
  List<CatalogColor> colors = const [];
  List<Season> seasons = const [];
  List<Collection> collections = const [];
  List<Branch> branches = const [];
  String searchQuery = '';
  String? branchId;
  String? categoryId;
  String? sizeId;
  String? colorId;
  String? seasonId;
  String? collectionId;

  Future<void> load() async {
    status = CatalogStatus.loading;
    errorMessage = null;
    notifyListeners();

    try {
      branches = await _api.getBranches();
      branchId ??= branches
          .where((branch) => branch.isDefault && branch.isActive)
          .firstOrNull
          ?.id;
      await Future.wait([_loadProducts(), _loadFilters()]);
      status = CatalogStatus.ready;
      notifyListeners();
    } catch (error) {
      status = CatalogStatus.error;
      errorMessage = _messageFor(error);
      notifyListeners();
    }
  }

  Future<void> updateFilters({
    String? branchId,
    String? categoryId,
    String? sizeId,
    String? colorId,
    String? seasonId,
    String? collectionId,
  }) async {
    this.branchId = branchId;
    this.categoryId = categoryId;
    this.sizeId = sizeId;
    this.colorId = colorId;
    this.seasonId = seasonId;
    this.collectionId = collectionId;
    await _reloadProducts();
  }

  Future<void> search(String value) async {
    searchQuery = value.trim();
    await _reloadProducts();
  }

  Future<void> clearFilters() {
    searchQuery = '';
    return updateFilters();
  }

  Future<void> _loadProducts() async {
    products = await _api.getProducts(
      query: searchQuery,
      branchId: branchId,
      categoryId: categoryId,
      sizeId: sizeId,
      colorId: colorId,
      seasonId: seasonId,
      collectionId: collectionId,
    );
  }

  Future<void> _loadFilters() async {
    final results = await Future.wait([
      _api.getCategories(),
      _api.getSizes(),
      _api.getColors(),
      _api.getSeasons(),
      _api.getCollections(),
    ]);
    categories = results[0] as List<Category>;
    sizes = results[1] as List<Size>;
    colors = results[2] as List<CatalogColor>;
    seasons = results[3] as List<Season>;
    collections = results[4] as List<Collection>;
  }

  Future<void> _reloadProducts() async {
    status = CatalogStatus.loading;
    errorMessage = null;
    notifyListeners();
    try {
      await _loadProducts();
      status = CatalogStatus.ready;
    } catch (error) {
      status = CatalogStatus.error;
      errorMessage = _messageFor(error);
    }
    notifyListeners();
  }

  static String _messageFor(Object error) {
    if (error is ApiException) {
      return error.message;
    }
    return 'No se pudo cargar el catálogo.';
  }
}
