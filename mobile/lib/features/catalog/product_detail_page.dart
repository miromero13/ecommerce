import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/storage/session_storage.dart';
import '../auth/auth_controller.dart';
import '../auth/login_dialog.dart';
import '../cart/cart_api.dart';
import '../reservations/reservation_models.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_image.dart';
import '../../shared/widgets/product_price.dart';
import '../../shared/widgets/quantity_selector.dart';
import '../../shared/widgets/variant_selector.dart';
import '../wishlist/wishlist_api.dart';
import 'catalog_models.dart';
import 'virtual_try_on_page.dart';

class ProductDetailArguments {
  const ProductDetailArguments({
    required this.product,
    this.sizes = const [],
    this.colors = const [],
    this.branches = const [],
    this.tenants = const [],
    this.branchId,
    this.reservationArguments,
  });

  final Product product;
  final List<Size> sizes;
  final List<CatalogColor> colors;
  final List<Branch> branches;
  final List<Tenant> tenants;
  final String? branchId;
  final ReservationArguments? reservationArguments;
}

class ProductDetailPage extends StatefulWidget {
  const ProductDetailPage({
    super.key,
    this.arguments,
    this.authController,
    this.cartApi,
    this.onAddToCart,
  });

  final ProductDetailArguments? arguments;
  final AuthController? authController;
  final CartApi? cartApi;
  final VoidCallback? onAddToCart;

  @override
  State<ProductDetailPage> createState() => _ProductDetailPageState();
}

class _ProductDetailPageState extends State<ProductDetailPage> {
  int _selectedVariantIndex = 0;
  int _quantity = 1;
  bool _addingToCart = false;
  bool? _saved; // CU16: null until the wishlist is known (or no session)
  bool _savingWish = false;

  WishlistApi? get _wishlistApi {
    final auth = widget.authController;
    if (auth == null || !auth.isAuthenticated) return null;
    return WishlistApi(
      client: ApiClient(tokenProvider: () => auth.accessToken, onUnauthorized: auth.handleUnauthorized),
    );
  }

  @override
  void initState() {
    super.initState();
    _loadSaved();
  }

  Future<void> _loadSaved() async {
    final api = _wishlistApi;
    final productId = _product?.id;
    if (api == null || productId == null) return;
    try {
      final items = await api.list();
      if (mounted) setState(() => _saved = items.any((row) => row['product_id'].toString() == productId));
    } catch (_) {
      // No heart if the wishlist cannot be read (e.g. staff account).
    }
  }

  Future<void> _toggleSaved() async {
    final api = _wishlistApi;
    final productId = _product?.id;
    if (api == null || productId == null || _saved == null) return;
    setState(() => _savingWish = true);
    try {
      final message = _saved! ? await api.remove(productId) : await api.add(productId);
      if (!mounted) return;
      setState(() => _saved = !_saved!);
      AppSnackBar.show(context, message, tone: AppSnackBarTone.success);
    } on ApiException catch (error) {
      if (mounted) AppSnackBar.show(context, error.message, tone: AppSnackBarTone.error);
    } finally {
      if (mounted) setState(() => _savingWish = false);
    }
  }

  Product? get _product => widget.arguments?.product;

  List<ProductVariant> get _variants => _product?.variants ?? const [];

  ProductVariant? get _selectedVariant => _variants.isEmpty
      ? null
      : _variants[_selectedVariantIndex.clamp(0, _variants.length - 1).toInt()];

  @override
  Widget build(BuildContext context) {
    final product = _product;
    if (product == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Detalle de producto')),
        body: const Center(
          child: Padding(
            padding: EdgeInsets.all(20),
            child: Text('El detalle reutilizará el producto del catálogo.'),
          ),
        ),
      );
    }

    final variant = _selectedVariant;
    final imageUrl = variant?.imageUrl ?? product.imageUrl;
    final price = variant?.price ?? 0;
    final status = variant?.status ?? product.status;
    final quantity = variant?.branchQuantity ?? product.branchQuantity;
    final branch = _branchName(widget.arguments!);

    return Scaffold(
      appBar: AppBar(title: const Text('Detalle de producto')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          AspectRatio(
            aspectRatio: 1,
            child: ProductImage(
              imageUrl: imageUrl,
              borderRadius: const BorderRadius.all(Radius.circular(12)),
            ),
          ),
          if (_variants.length > 1) ...[
            const SizedBox(height: 12),
            _imageGallery(),
          ],
          const SizedBox(height: 24),
          AppSectionTitle(
            title: product.name,
            subtitle: product.sku ?? 'Producto FashionStore',
            action: _saved == null
                ? null
                : IconButton(
                    tooltip: _saved! ? 'Quitar de mi lista de deseos' : 'Añadir a mi lista de deseos',
                    onPressed: _savingWish ? null : _toggleSaved,
                    icon: Icon(_saved! ? Icons.favorite : Icons.favorite_border, color: Colors.pink),
                  ),
          ),
          const SizedBox(height: 12),
          ProductPrice(price: price, originalPrice: variant?.originalPrice),
          if (product.description != null &&
              product.description!.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(product.description!),
          ],
          const SizedBox(height: 20),
          if (_variants.isNotEmpty) _variantOptions(),
          const SizedBox(height: 20),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Información de la variante',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                _detailLine(
                  'SKU',
                  variant?.sku ?? product.sku ?? 'No disponible',
                ),
                _detailLine(
                  'Talla',
                  _sizeName(variant?.sizeId ?? product.sizeId),
                ),
                _detailLine(
                  'Color',
                  _colorName(variant?.colorId ?? product.colorId),
                ),
                _detailLine('Estado', _statusName(status)),
                _detailLine('Disponibilidad', _availability(quantity, branch)),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Cantidad', style: Theme.of(context).textTheme.titleMedium),
              QuantitySelector(
                value: _quantity,
                max: _quantityLimit(quantity),
                onChanged: (value) => setState(() => _quantity = value),
              ),
            ],
          ),
          const SizedBox(height: 20),
          AppButton(
            label: 'Agregar al carrito',
            icon: const Icon(Icons.shopping_bag_outlined),
            onPressed:
                widget.onAddToCart ??
                (_canAddToCart(variant, quantity) ? _addToCart : null),
            isLoading: _addingToCart,
            expand: true,
          ),
          const SizedBox(height: 12),
          AppButton(
            label: 'Reservar prenda',
            icon: const Icon(Icons.bookmark_add_outlined),
            onPressed: _canReserve(product, variant) ? _reserveGarment : null,
            variant: AppButtonVariant.outlined,
            expand: true,
          ),
          // Only when the selling company's plan includes the virtual try-on.
          if (product.tryOnEnabled &&
              imageUrl != null &&
              imageUrl.trim().isNotEmpty) ...[
            const SizedBox(height: 12),
            AppButton(
              label: 'Probar prenda',
              icon: const Icon(Icons.checkroom_outlined),
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => VirtualTryOnPage(
                      productName: product.name,
                      garmentImageUrl: imageUrl,
                    ),
                  ),
                );
              },
              variant: AppButtonVariant.outlined,
              expand: true,
            ),
          ],
        ],
      ),
    );
  }

  Widget _imageGallery() {
    return SizedBox(
      height: 76,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: _variants.length,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final variant = _variants[index];
          return InkWell(
            onTap: () => _selectVariant(index),
            borderRadius: BorderRadius.circular(8),
            child: SizedBox(
              width: 76,
              child: ProductImage(
                imageUrl: variant.imageUrl,
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _variantOptions() {
    return AppVariantSelector(
      options: [
        for (var index = 0; index < _variants.length; index++)
          AppVariantOption(
            id: _variants[index].id,
            label: _variantLabel(_variants[index]),
          ),
      ],
      selectedId: _selectedVariant?.id,
      onChanged: (variantId) {
        final index = _variants.indexWhere(
          (variant) => variant.id == variantId,
        );
        if (index >= 0) _selectVariant(index);
      },
    );
  }

  void _selectVariant(int index) {
    final maxQuantity = _quantityLimit(_variants[index].branchQuantity);
    setState(() {
      _selectedVariantIndex = index;
      if (_quantity > maxQuantity) _quantity = maxQuantity;
    });
  }

  String _variantLabel(ProductVariant variant) {
    final labels = [
      _sizeName(variant.sizeId),
      _colorName(variant.colorId),
    ].where((label) => label != 'No disponible');
    final suffix = labels.isEmpty ? '' : '${labels.join(' · ')} · ';
    return '$suffix${variant.sku}';
  }

  String _sizeName(String? id) {
    if (id == null) return 'No disponible';
    return widget.arguments!.sizes
            .where((size) => size.id == id)
            .firstOrNull
            ?.name ??
        id;
  }

  String _colorName(String? id) {
    if (id == null) return 'No disponible';
    return widget.arguments!.colors
            .where((color) => color.id == id)
            .firstOrNull
            ?.name ??
        id;
  }

  String _statusName(ProductStatus? status) {
    return switch (status) {
      ProductStatus.active => 'Activo',
      ProductStatus.pending => 'Pendiente',
      ProductStatus.inactive => 'Inactivo',
      null => 'No disponible',
    };
  }

  String _availability(int? quantity, String? branch) {
    final suffix = branch == null ? '' : ' en $branch';
    return switch (quantity) {
      null => 'No consultada$suffix',
      > 0 => 'Disponible ($quantity)$suffix',
      _ => 'Agotado$suffix',
    };
  }

  int _quantityLimit(int? quantity) {
    if (quantity == null) return 99;
    return quantity > 0 ? quantity : 1;
  }

  bool _canAddToCart(ProductVariant? variant, int? quantity) {
    return widget.authController != null &&
        variant != null &&
        (quantity == null || quantity > 0);
  }

  bool _canReserve(Product? product, ProductVariant? variant) {
    return widget.authController != null && product != null && variant != null;
  }

  Branch? _resolveBranch() {
    final args = widget.arguments;
    if (args == null) return null;
    if (args.branchId != null) {
      final match =
          args.branches.where((b) => b.id == args.branchId).firstOrNull;
      if (match != null) return match;
    }
    final productTenantId = _product?.tenantId;
    if (productTenantId != null) {
      final match =
          args.branches.where((b) => b.tenantId == productTenantId).firstOrNull;
      if (match != null) return match;
    }
    return args.branches.firstOrNull;
  }

  String _resolveTenantName(Branch? branch) {
    final args = widget.arguments;
    final tenantId = _product?.tenantId ?? branch?.tenantId;
    if (tenantId != null && args != null) {
      final match = args.tenants.where((t) => t.id == tenantId).firstOrNull;
      if (match != null) return match.name;
    }
    return 'Tienda';
  }

  Future<void> _reserveGarment() async {
    final product = _product;
    final variant = _selectedVariant;
    if (!_canReserve(product, variant)) return;

    final branch = _resolveBranch();
    final tenantName = _resolveTenantName(branch);
    final targetBranchId = branch?.id;
    final targetBranchName =
        branch != null ? '${branch.name} (${branch.city})' : 'Sucursal';

    final reservationArgs = widget.arguments?.reservationArguments;
    final currentBranchId = reservationArgs?.branchId;
    final currentBranchName = reservationArgs?.branchName;
    final currentTenantName = reservationArgs?.tenantName;

    List<ReservationDraftItem> items = [...?reservationArgs?.items];

    if (items.isNotEmpty &&
        currentBranchId != null &&
        targetBranchId != null &&
        currentBranchId != targetBranchId) {
      final currentFullName =
          currentTenantName != null && currentTenantName.isNotEmpty
              ? '$currentTenantName — $currentBranchName'
              : (currentBranchName ?? 'otra sucursal');

      final confirm = await showDialog<bool>(
        context: context,
        builder: (dialogCtx) => AlertDialog(
          title: const Text('¿Cambiar de sucursal?'),
          content: Text(
            'Ya tenés prendas para reservar en $currentFullName.\n\n'
            'Si continuás, se reiniciará tu reserva con la nueva sucursal $tenantName — $targetBranchName.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogCtx).pop(false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogCtx).pop(true),
              child: const Text('Cambiar y reservar'),
            ),
          ],
        ),
      );

      if (confirm != true) return;
      items = [];
    }

    final selectedItem = ReservationDraftItem(
      variantId: variant!.id,
      quantity: _quantity,
      productName: product!.name,
      variantSku: variant.sku.isEmpty ? product.sku : variant.sku,
      imageUrl: variant.imageUrl ?? product.imageUrl,
    );

    final existingIndex = items.indexWhere(
      (item) => item.variantId == selectedItem.variantId,
    );
    if (existingIndex == -1) {
      items.add(selectedItem);
    } else {
      final existing = items[existingIndex];
      items[existingIndex] = ReservationDraftItem(
        variantId: existing.variantId,
        quantity: existing.quantity + selectedItem.quantity,
        productName: selectedItem.productName ?? existing.productName,
        variantSku: selectedItem.variantSku ?? existing.variantSku,
        imageUrl: selectedItem.imageUrl ?? existing.imageUrl,
      );
    }

    final updatedArguments = ReservationArguments(
      items: items,
      branchId: targetBranchId ?? currentBranchId,
      branchName: targetBranchName,
      tenantName: tenantName,
    );
    if (!mounted) return;
    Navigator.of(context).pop(updatedArguments);
  }

  Future<void> _addToCart() async {
    final product = _product;
    final variant = _selectedVariant;
    final authController = widget.authController;
    if (product == null || variant == null || authController == null) return;

    final branch = _resolveBranch();
    final tenantName = _resolveTenantName(branch);
    final targetBranchId = branch?.id;
    final targetBranchName =
        branch != null ? '${branch.name} (${branch.city})' : 'Sucursal';

    setState(() => _addingToCart = true);
    try {
      if (!authController.isAuthenticated) {
        final loggedIn = await LoginDialog.show(
          context: context,
          controller: authController,
        );
        if (!mounted || loggedIn != true || !authController.isAuthenticated) {
          return;
        }
      }

      final sessionStorage = const SessionStorage();
      final cartContext = await sessionStorage.readCartContext();

      final api =
          widget.cartApi ??
          CartApi(
            tokenProvider: () => authController.accessToken,
            onUnauthorized: authController.handleUnauthorized,
          );

      if (!mounted) return;
      // One cart per company: the backend rejects another company's item with a clear message.

      final result = await api.addItem(
        variantId: variant.id,
        quantity: _quantity,
      );

      if (targetBranchId != null && cartContext == null) {
        // Remember the first branch only, to preselect pickup at checkout.
        await sessionStorage.saveCartContext(
          branchId: targetBranchId,
          branchName: targetBranchName,
          tenantName: tenantName,
        );
      }

      if (mounted) {
        AppSnackBar.show(
          context,
          result.message,
          tone: AppSnackBarTone.success,
        );
      }
    } catch (error) {
      if (mounted) {
        final message = error is ApiException
            ? error.message
            : 'No se pudo agregar el producto al carrito.';
        AppSnackBar.show(context, message, tone: AppSnackBarTone.error);
      }
    } finally {
      if (mounted) setState(() => _addingToCart = false);
    }
  }

  String? _branchName(ProductDetailArguments arguments) {
    final id = arguments.branchId;
    if (id == null) return null;
    return arguments.branches
        .where((branch) => branch.id == id)
        .firstOrNull
        ?.name;
  }

  Widget _detailLine(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 116,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
