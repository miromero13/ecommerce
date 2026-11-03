import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_image.dart';
import '../auth/auth_controller.dart';
import 'wishlist_api.dart';

class _WishlistBranchGroup {
  _WishlistBranchGroup({
    required this.tenantId,
    required this.tenantName,
    required this.branchId,
    required this.branchName,
    required this.items,
  });

  final String tenantId;
  final String tenantName;
  final String branchId;
  final String branchName;
  final List<Map<String, dynamic>> items;
}

/// CU16: favorites of the customer grouped by company and branch.
class WishlistPage extends StatefulWidget {
  const WishlistPage({super.key, required this.authController});

  final AuthController authController;

  @override
  State<WishlistPage> createState() => _WishlistPageState();
}

class _WishlistPageState extends State<WishlistPage> {
  late final WishlistApi _api = WishlistApi(
    client: ApiClient(
      tokenProvider: () => widget.authController.accessToken,
      onUnauthorized: widget.authController.handleUnauthorized,
    ),
  );
  List<Map<String, dynamic>>? _items;
  final Map<String, String> _chosen = {};
  String? _busyId;
  String? _busyBranchId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final items = await _api.list();
      if (mounted) setState(() => _items = items);
    } catch (error) {
      if (!mounted) return;
      setState(() => _items = const []);
      _show(error, 'No se pudo cargar tu lista de deseos.');
    }
  }

  List<Map<String, dynamic>> _variants(Map<String, dynamic> item) =>
      (item['variants'] as List).map((v) => Map<String, dynamic>.from(v as Map)).toList();

  String? _variantFor(Map<String, dynamic> item) {
    final productId = item['product_id'].toString();
    return _chosen[productId] ??
        _variants(item).where((v) => (v['available'] as num) > 0).map((v) => v['id'].toString()).firstOrNull;
  }

  List<_WishlistBranchGroup> _buildGroups(List<Map<String, dynamic>> items) {
    final map = <String, _WishlistBranchGroup>{};

    for (final item in items) {
      final tenantId = item['tenant_id']?.toString() ?? '';
      final tenantName = item['tenant_name']?.toString() ?? 'Tienda';
      final branches = (item['available_branches'] as List?) ?? [];

      if (branches.isEmpty) {
        final key = '${tenantId}_none';
        map.putIfAbsent(
          key,
          () => _WishlistBranchGroup(
            tenantId: tenantId,
            tenantName: tenantName,
            branchId: '',
            branchName: 'Sin sucursal asignada',
            items: [],
          ),
        ).items.add(item);
      } else {
        for (final br in branches) {
          final branchMap = Map<String, dynamic>.from(br as Map);
          final branchId = branchMap['branch_id']?.toString() ?? '';
          final branchName =
              '${branchMap['branch_name'] ?? ''} (${branchMap['city'] ?? ''})'.trim();
          final key = '${tenantId}_$branchId';
          map.putIfAbsent(
            key,
            () => _WishlistBranchGroup(
              tenantId: tenantId,
              tenantName: tenantName,
              branchId: branchId,
              branchName: branchName,
              items: [],
            ),
          ).items.add(item);
        }
      }
    }

    return map.values.toList();
  }

  Future<void> _moveAll(_WishlistBranchGroup group) async {
    setState(() => _busyBranchId = group.branchId);
    try {
      final message = await _api.moveAllToCart(group.tenantId, group.branchId);
      if (mounted) {
        AppSnackBar.show(context, message, tone: AppSnackBarTone.success);
      }
      await _load();
    } catch (error) {
      _show(error, 'No se pudieron mover las prendas al carrito.');
    } finally {
      if (mounted) setState(() => _busyBranchId = null);
    }
  }

  Future<void> _run(String productId, Future<String> Function() action, String fallback) async {
    setState(() => _busyId = productId);
    try {
      final message = await action();
      if (mounted) AppSnackBar.show(context, message, tone: AppSnackBarTone.success);
      await _load();
    } catch (error) {
      _show(error, fallback);
    } finally {
      if (mounted) setState(() => _busyId = null);
    }
  }

  void _show(Object error, String fallback) {
    if (!mounted) return;
    AppSnackBar.show(context, error is ApiException ? error.message : fallback, tone: AppSnackBarTone.error);
  }

  @override
  Widget build(BuildContext context) {
    final items = _items;
    if (items == null) return const AppLoading();
    final groups = _buildGroups(items);

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const AppSectionTitle(
            title: 'Lista de deseos',
            subtitle: 'Prendas favoritas organizadas por empresa y sucursal.',
          ),
          const SizedBox(height: 16),
          if (items.isEmpty)
            const AppEmptyView(
              title: 'Aún no guardaste prendas',
              message: 'Usa el corazón en el catálogo para añadirlas.',
            ),
          for (final group in groups) ...[
            _groupCard(group),
            const SizedBox(height: 20),
          ],
        ],
      ),
    );
  }

  Widget _groupCard(_WishlistBranchGroup group) {
    final isGroupBusy = _busyBranchId == group.branchId;

    return Container(
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade300),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header de la empresa y sucursal
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.storefront, size: 16, color: Colors.blueGrey),
                        const SizedBox(width: 4),
                        Flexible(
                          child: Text(
                            group.tenantName,
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: Colors.black87,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        const Icon(Icons.place_outlined, size: 14, color: Colors.grey),
                        const SizedBox(width: 4),
                        Flexible(
                          child: Text(
                            group.branchName,
                            style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (group.branchId.isNotEmpty)
                AppButton(
                  label: 'Agregar todo (${group.items.length})',
                  icon: const Icon(Icons.shopping_cart_outlined, size: 16),
                  isLoading: isGroupBusy,
                  onPressed: isGroupBusy ? null : () => _moveAll(group),
                ),
            ],
          ),
          const Divider(height: 20),
          // Items de esa sucursal
          for (final item in group.items) ...[
            _itemCard(item, group.branchId),
            const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }

  Widget _itemCard(Map<String, dynamic> item, String branchId) {
    final productId = item['product_id'].toString();
    final variants = _variants(item);
    final inStock = item['in_stock'] == true;
    final busy = _busyId == productId;

    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 72,
            height: 72,
            child: ProductImage(imageUrl: item['image_url'] as String?),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item['product_name'].toString(),
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 2),
                Text(
                  '${item['price'] ?? '-'} BOB',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                if (inStock) ...[
                  const SizedBox(height: 6),
                  DropdownButton<String>(
                    isExpanded: true,
                    value: _variantFor(item),
                    items: [
                      for (final v in variants)
                        DropdownMenuItem(
                          value: v['id'].toString(),
                          enabled: (v['available'] as num) > 0,
                          child: Text(
                            '${v['size'] ?? 'Única'} · ${v['color'] ?? 'Sin color'}'
                            '${(v['available'] as num) > 0 ? '' : ' (agotado)'}',
                            style: const TextStyle(fontSize: 12),
                          ),
                        ),
                    ],
                    onChanged: (value) => setState(() => _chosen[productId] = value!),
                  ),
                ] else
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 4),
                    child: Text('Sin stock por ahora', style: TextStyle(color: Colors.orange)),
                  ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  children: [
                    FilledButton(
                      onPressed: !inStock || busy || _variantFor(item) == null
                          ? null
                          : () => _run(
                              productId,
                              () => _api.moveToCart(
                                productId,
                                _variantFor(item)!,
                                branchId: branchId.isNotEmpty ? branchId : null,
                              ),
                              'No se pudo mover la prenda al carrito.',
                            ),
                      child: const Text('Mover al carrito', style: TextStyle(fontSize: 12)),
                    ),
                    OutlinedButton(
                      onPressed: busy ? null : () => _run(productId, () => _api.remove(productId), 'No se pudo quitar la prenda.'),
                      child: const Text('Quitar', style: TextStyle(fontSize: 12)),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
