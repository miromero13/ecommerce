import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../network/api_client.dart';
import 'offline_catalog_models.dart';

class OfflineCatalogService {
  OfflineCatalogService({
    required ApiClient apiClient,
    FlutterSecureStorage? storage,
  })  : _api = apiClient,
        _storage = storage ?? const FlutterSecureStorage();

  static const _catalogCacheKey = 'offline_cached_catalog_json';
  static const _catalogSyncTimestampKey = 'offline_catalog_sync_timestamp';

  final ApiClient _api;
  final FlutterSecureStorage _storage;

  List<OfflineCatalogProduct> _cachedProducts = [];
  DateTime? _lastSync;

  List<OfflineCatalogProduct> get cachedProducts => List.unmodifiable(_cachedProducts);
  int get cachedCount => _cachedProducts.length;
  DateTime? get lastSync => _lastSync;

  /// CU23: Descarga el catálogo optimizado y lo persiste localmente en el dispositivo
  Future<int> syncCatalog({String? branchId}) async {
    try {
      final query = <String, dynamic>{};
      if (branchId != null && branchId.isNotEmpty) {
        query['branch_id'] = branchId;
      }

      final res = await _api.get<Map<String, dynamic>>(
        '/api/offline/catalog-sync',
        queryParameters: query,
        parser: (data) => data as Map<String, dynamic>,
      );

      final rawList = (res.data?['products'] as List<dynamic>?) ?? [];
      final products = rawList
          .whereType<Map<String, dynamic>>()
          .map((item) => OfflineCatalogProduct.fromJson(item))
          .toList();

      _cachedProducts = products;
      _lastSync = DateTime.now();

      final encoded = jsonEncode(products.map((p) => p.toJson()).toList());
      await _storage.write(key: _catalogCacheKey, value: encoded);
      await _storage.write(
        key: _catalogSyncTimestampKey,
        value: _lastSync!.toIso8601String(),
      );

      return products.length;
    } catch (_) {
      // Fallback a los datos ya cacheados si falla la red
      await loadLocalCatalog();
      return _cachedProducts.length;
    }
  }

  /// Carga el catálogo guardado en almacenamiento local
  Future<List<OfflineCatalogProduct>> loadLocalCatalog() async {
    try {
      final jsonStr = await _storage.read(key: _catalogCacheKey);
      final timestampStr = await _storage.read(key: _catalogSyncTimestampKey);

      if (timestampStr != null) {
        _lastSync = DateTime.tryParse(timestampStr);
      }

      if (jsonStr != null && jsonStr.isNotEmpty) {
        final decoded = jsonDecode(jsonStr) as List<dynamic>;
        _cachedProducts = decoded
            .whereType<Map<String, dynamic>>()
            .map((item) => OfflineCatalogProduct.fromJson(item))
            .toList();
      }
    } catch (_) {
      _cachedProducts = [];
    }
    return _cachedProducts;
  }

  /// Búsqueda rápida offline en memoria
  List<OfflineCatalogProduct> searchProducts(String query, {String? category}) {
    final cleanQuery = query.trim().toLowerCase();
    final cleanCategory = category?.trim().toLowerCase();

    return _cachedProducts.where((product) {
      if (cleanCategory != null &&
          cleanCategory.isNotEmpty &&
          cleanCategory != 'todos' &&
          !product.category.toLowerCase().contains(cleanCategory)) {
        return false;
      }

      if (cleanQuery.isEmpty) return true;

      final nameMatch = product.name.toLowerCase().contains(cleanQuery);
      final descMatch = product.description.toLowerCase().contains(cleanQuery);
      final skuMatch = product.variants.any((v) => v.sku.toLowerCase().contains(cleanQuery));

      return nameMatch || descMatch || skuMatch;
    }).toList();
  }
}
