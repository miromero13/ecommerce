import 'package:flutter/material.dart';

import '../../core/network/api_exception.dart';
import '../auth/auth_controller.dart';
import '../auth/login_dialog.dart';
import '../cart/cart_api.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_image.dart';
import '../../shared/widgets/product_price.dart';
import '../../shared/widgets/quantity_selector.dart';
import '../../shared/widgets/variant_selector.dart';
import 'catalog_models.dart';

class ProductDetailArguments {
  const ProductDetailArguments({
    required this.product,
    this.sizes = const [],
    this.colors = const [],
    this.branches = const [],
    this.branchId,
  });

  final Product product;
  final List<Size> sizes;
  final List<CatalogColor> colors;
  final List<Branch> branches;
  final String? branchId;
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
    final imageUrl =
        variant?.imageUrl ?? (_variants.isEmpty ? product.imageUrl : null);
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

  Future<void> _addToCart() async {
    final product = _product;
    final variant = _selectedVariant;
    final authController = widget.authController;
    if (product == null || variant == null || authController == null) return;

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

      final api =
          widget.cartApi ??
          CartApi(
            tokenProvider: () => authController.accessToken,
            onUnauthorized: authController.handleUnauthorized,
          );
      final result = await api.addItem(
        variantId: variant.id,
        quantity: _quantity,
      );
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
