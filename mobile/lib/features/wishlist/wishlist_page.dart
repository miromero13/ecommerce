import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_image.dart';
import '../auth/auth_controller.dart';
import 'wishlist_api.dart';

/// CU16: favorites of the customer; each one can be moved to the cart choosing size/color.
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

  /// Default to the first variant with stock.
  String? _variantFor(Map<String, dynamic> item) {
    final productId = item['product_id'].toString();
    return _chosen[productId] ??
        _variants(item).where((v) => (v['available'] as num) > 0).map((v) => v['id'].toString()).firstOrNull;
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
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const AppSectionTitle(title: 'Lista de deseos', subtitle: 'Tus prendas favoritas.'),
          const SizedBox(height: 16),
          if (items.isEmpty)
            const AppEmptyView(
              title: 'Aún no guardaste prendas',
              message: 'Usa el corazón en el detalle de una prenda para añadirla.',
            ),
          for (final item in items) ...[_itemCard(item), const SizedBox(height: 12)],
        ],
      ),
    );
  }

  Widget _itemCard(Map<String, dynamic> item) {
    final productId = item['product_id'].toString();
    final variants = _variants(item);
    final inStock = item['in_stock'] == true;
    final busy = _busyId == productId;
    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 72, height: 72, child: ProductImage(imageUrl: item['image_url'] as String?)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item['product_name'].toString(), style: Theme.of(context).textTheme.titleSmall),
                Text('${item['tenant_name'] ?? ''} · ${item['price'] ?? '-'} BOB'),
                if (inStock)
                  DropdownButton<String>(
                    isExpanded: true,
                    value: _variantFor(item),
                    items: [
                      for (final v in variants)
                        DropdownMenuItem(
                          value: v['id'].toString(),
                          enabled: (v['available'] as num) > 0,
                          child: Text('${v['size'] ?? 'Única'} · ${v['color'] ?? 'Sin color'}'
                              '${(v['available'] as num) > 0 ? '' : ' (agotado)'}'),
                        ),
                    ],
                    onChanged: (value) => setState(() => _chosen[productId] = value!),
                  )
                else
                  const Text('Sin stock por ahora'),
                Wrap(
                  spacing: 8,
                  children: [
                    FilledButton(
                      onPressed: !inStock || busy || _variantFor(item) == null
                          ? null
                          : () => _run(productId, () => _api.moveToCart(productId, _variantFor(item)!),
                              'No se pudo mover la prenda al carrito.'),
                      child: const Text('Mover al carrito'),
                    ),
                    OutlinedButton(
                      onPressed: busy ? null : () => _run(productId, () => _api.remove(productId), 'No se pudo quitar la prenda.'),
                      child: const Text('Quitar'),
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
