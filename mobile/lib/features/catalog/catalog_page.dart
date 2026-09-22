import 'dart:async';

import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/filter_chip.dart';
import '../../shared/widgets/product_card.dart';
import '../auth/auth_controller.dart';
import '../chatbot/chatbot_page.dart';
import '../reservations/reservation_models.dart';
import 'catalog_api.dart';
import 'catalog_controller.dart';
import 'catalog_models.dart';
import 'product_detail_page.dart';

class CatalogPage extends StatefulWidget {
  const CatalogPage({
    super.key,
    this.controller,
    this.authController,
    this.reservationArguments,
  });

  final CatalogController? controller;
  final AuthController? authController;
  final ReservationArguments? reservationArguments;

  @override
  State<CatalogPage> createState() => _CatalogPageState();
}

class _CatalogPageState extends State<CatalogPage> {
  late final CatalogController _controller;
  late final bool _ownsController;
  late final CatalogApi _authenticatedApi;
  late final TextEditingController _searchController;
  late List<ReservationDraftItem> _reservationItems;
  List<Product> _recommendedProducts = const [];
  var _recommendationsRequestVersion = 0;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller = widget.controller ?? CatalogController();
    _authenticatedApi = CatalogApi(
      tokenProvider: () => widget.authController?.accessToken,
      onUnauthorized: widget.authController?.handleUnauthorized,
    );
    _searchController = TextEditingController();
    _reservationItems = [...?widget.reservationArguments?.items];
    if (_controller.status == CatalogStatus.idle) {
      unawaited(
        _controller.load().then((_) {
          if (mounted) unawaited(_loadRecommendations());
        }),
      );
    } else if (_controller.status == CatalogStatus.ready) {
      unawaited(_loadRecommendations());
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    if (_ownsController) _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _controller,
      builder: (context, _) => Stack(
        children: [
          ListView(
            padding: const EdgeInsets.all(20),
            children: [
              const AppSectionTitle(
                title: 'Catálogo público',
                subtitle: 'Explora las prendas disponibles en FashionStore.',
              ),
              const SizedBox(height: 20),
              _shortcuts(),
              const SizedBox(height: 20),
              _searchField(),
              const SizedBox(height: 12),
              _branchSelector(),
              if (_controller.status == CatalogStatus.ready) ...[
                const SizedBox(height: 8),
                _filters(),
              ],
              const SizedBox(height: 16),
              _content(),
            ],
          ),
          if (_isCliente)
            ChatbotAssistant(
              authController: widget.authController!,
              onOpenProduct: _openProductById,
            ),
        ],
      ),
    );
  }

  Widget _searchField() {
    return TextField(
      controller: _searchController,
      textInputAction: TextInputAction.search,
      onSubmitted: _search,
      decoration: InputDecoration(
        hintText: 'Buscar productos',
        prefixIcon: const Icon(Icons.search),
        suffixIcon: IconButton(
          tooltip: 'Buscar',
          onPressed: () => _search(_searchController.text),
          icon: const Icon(Icons.arrow_forward),
        ),
      ),
    );
  }

  Widget _shortcuts() {
    return Row(
      children: [
        Expanded(
          child: AppButton(
            label: 'Carrito',
            icon: const Icon(Icons.shopping_bag_outlined),
            onPressed: () => Navigator.of(context).pushNamed(AppRoutes.cart),
            expand: true,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: AppButton(
            label: 'Reservas',
            icon: const Icon(Icons.event_available_outlined),
            onPressed: () => Navigator.of(context).pushNamed(
              AppRoutes.reservationCreate,
              arguments: ReservationArguments(
                items: List.of(_reservationItems),
              ),
            ),
            expand: true,
          ),
        ),
      ],
    );
  }

  Widget _branchSelector() {
    return DropdownButtonFormField<String>(
      initialValue: _controller.branchId ?? '',
      isExpanded: true,
      decoration: const InputDecoration(
        labelText: 'Sucursal',
        prefixIcon: Icon(Icons.location_on_outlined),
      ),
      items: [
        const DropdownMenuItem(
          value: '',
          child: Text('Todas las sucursales', overflow: TextOverflow.ellipsis),
        ),
        ..._controller.branches.map(
          (branch) => DropdownMenuItem(
            value: branch.id,
            child: Text(
              '${branch.name} · ${branch.city}',
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),
      ],
      onChanged: _controller.status == CatalogStatus.loading
          ? null
          : (value) => _updateFilters(branchId: value),
    );
  }

  Widget _filters() {
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: const Text('Filtros'),
      childrenPadding: const EdgeInsets.only(bottom: 4),
      children: [
        Align(
          alignment: Alignment.centerLeft,
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final category in _controller.categories)
                AppFilterChip(
                  label: category.name,
                  selected: category.id == _controller.categoryId,
                  onSelected: (selected) =>
                      _updateFilters(categoryId: selected ? category.id : ''),
                ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        _filterDropdown<Size>(
          label: 'Talla',
          value: _controller.sizeId,
          items: _controller.sizes,
          id: (item) => item.id,
          name: (item) => item.name,
          onChanged: (value) => _updateFilters(sizeId: value),
        ),
        const SizedBox(height: 12),
        _filterDropdown<CatalogColor>(
          label: 'Color',
          value: _controller.colorId,
          items: _controller.colors,
          id: (item) => item.id,
          name: (item) => item.name,
          onChanged: (value) => _updateFilters(colorId: value),
        ),
        const SizedBox(height: 12),
        _filterDropdown<Season>(
          label: 'Temporada',
          value: _controller.seasonId,
          items: _controller.seasons,
          id: (item) => item.id,
          name: (item) => item.name,
          onChanged: (value) => _updateFilters(seasonId: value),
        ),
        const SizedBox(height: 12),
        _filterDropdown<Collection>(
          label: 'Colección',
          value: _controller.collectionId,
          items: _controller.collections,
          id: (item) => item.id,
          name: (item) => item.name,
          onChanged: (value) => _updateFilters(collectionId: value),
        ),
        Align(
          alignment: Alignment.centerRight,
          child: TextButton(
            onPressed:
                _controller.searchQuery.isEmpty &&
                    _controller.branchId == null &&
                    _controller.categoryId == null &&
                    _controller.sizeId == null &&
                    _controller.colorId == null &&
                    _controller.seasonId == null &&
                    _controller.collectionId == null
                ? null
                : () {
                    _searchController.clear();
                    _controller.clearFilters();
                  },
            child: const Text('Limpiar filtros'),
          ),
        ),
      ],
    );
  }

  Widget _filterDropdown<T>({
    required String label,
    required String? value,
    required List<T> items,
    required String Function(T item) id,
    required String Function(T item) name,
    required ValueChanged<String?> onChanged,
  }) {
    return DropdownButtonFormField<String>(
      initialValue: value ?? '',
      isExpanded: true,
      decoration: InputDecoration(labelText: label),
      items: [
        const DropdownMenuItem(value: '', child: Text('Todos')),
        ...items.map(
          (item) => DropdownMenuItem(
            value: id(item),
            child: Text(name(item), overflow: TextOverflow.ellipsis),
          ),
        ),
      ],
      onChanged: onChanged,
    );
  }

  Widget _content() {
    return switch (_controller.status) {
      CatalogStatus.idle || CatalogStatus.loading => const Padding(
        padding: EdgeInsets.symmetric(vertical: 80),
        child: AppLoading(message: 'Cargando catálogo...'),
      ),
      CatalogStatus.error => Padding(
        padding: const EdgeInsets.symmetric(vertical: 40),
        child: AppErrorView(
          message: _controller.errorMessage ?? 'No se pudo cargar el catálogo.',
          onRetry: _retryCatalog,
        ),
      ),
      CatalogStatus.ready => _catalogContent(),
    };
  }

  Widget _catalogContent() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_recommendedProducts.isNotEmpty) ...[
          const AppSectionTitle(
            title: 'Recomendaciones para ti',
            subtitle: 'Prendas que podrían gustarte.',
          ),
          const SizedBox(height: 12),
          _recommendationCarousel(),
          const SizedBox(height: 24),
        ],
        if (_controller.products.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 80),
            child: AppEmptyView(
              message: 'No encontramos productos con esos filtros.',
            ),
          )
        else
          _productGrid(),
      ],
    );
  }

  Widget _recommendationCarousel() {
    return SizedBox(
      height: 300,
      child: Stack(
        children: [
          ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: _recommendedProducts.length,
            padding: const EdgeInsets.only(right: 42),
            separatorBuilder: (_, _) => const SizedBox(width: 12),
            itemBuilder: (context, index) => SizedBox(
              width: 180,
              child: _productCard(_recommendedProducts[index]),
            ),
          ),
          if (_recommendedProducts.length > 1)
            Positioned(
              top: 0,
              right: 0,
              bottom: 0,
              child: IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Theme.of(
                          context,
                        ).colorScheme.surface.withValues(alpha: 0),
                        Theme.of(context).colorScheme.surface,
                      ],
                    ),
                  ),
                  child: const SizedBox(
                    width: 48,
                    child: Center(child: Icon(Icons.swipe_outlined)),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _productGrid() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
        maxCrossAxisExtent: 260,
        mainAxisSpacing: 16,
        crossAxisSpacing: 16,
        childAspectRatio: .60,
      ),
      itemCount: _controller.products.length,
      itemBuilder: (context, index) =>
          _productCard(_controller.products[index]),
    );
  }

  Widget _productCard(Product product) {
    final variants = product.variants ?? const <ProductVariant>[];
    final primaryVariant = variants.isEmpty ? null : variants.first;
    final imageUrls = variants
        .where(
          (variant) =>
              variant.status == ProductStatus.active &&
              variant.imageUrl?.trim().isNotEmpty == true,
        )
        .map((variant) => variant.imageUrl!.trim())
        .toList(growable: false);
    final badge = product.branchQuantity == null
        ? null
        : product.branchQuantity! > 0
        ? 'Disponible'
        : 'Agotado';

    return ProductCard(
      name: product.name,
      price: primaryVariant?.price ?? 0,
      originalPrice: primaryVariant?.originalPrice,
      imageUrl: imageUrls.isEmpty ? product.imageUrl : null,
      variantImageUrls: imageUrls,
      badge: badge,
      onTap: () => _openProduct(product),
    );
  }

  Future<void> _openProduct(Product product) async {
    unawaited(_recordProductView(product));
    final result = await Navigator.of(context).pushNamed(
      AppRoutes.productDetail,
      arguments: ProductDetailArguments(
        product: product,
        sizes: _controller.sizes,
        colors: _controller.colors,
        branches: _controller.branches,
        branchId: _controller.branchId,
        reservationArguments: ReservationArguments(
          items: List.of(_reservationItems),
        ),
      ),
    );
    if (!mounted || result is! ReservationArguments) return;

    setState(() => _reservationItems = List.of(result.items));
    AppSnackBar.show(
      context,
      'Prenda agregada a la reserva.',
      tone: AppSnackBarTone.success,
    );
  }

  Future<void> _openProductById(String productId) async {
    try {
      final product = await _authenticatedApi.getProduct(
        productId,
        branchId: _controller.branchId,
      );
      if (mounted) await _openProduct(product);
    } catch (_) {
      if (mounted) {
        AppSnackBar.show(
          context,
          'No se pudo cargar el producto.',
          tone: AppSnackBarTone.error,
        );
      }
    }
  }

  Future<void> _recordProductView(Product product) async {
    if (!_isCliente) return;
    try {
      await _authenticatedApi.recordProductView(
        product.id,
        variantId: product.variants?.firstOrNull?.id,
        branchId: _controller.branchId,
      );
    } catch (_) {
      // View telemetry must never block catalog navigation.
    }
  }

  Future<void> _loadRecommendations() async {
    final requestVersion = ++_recommendationsRequestVersion;
    final authController = widget.authController;
    final user = authController?.user;
    if (!_isCliente || authController == null || user == null) {
      if (mounted) setState(() => _recommendedProducts = const []);
      return;
    }

    try {
      final recommendations = await _authenticatedApi
          .getCollaborativeRecommendations(
            userId: user.id,
            branchId: _controller.branchId,
          );
      final catalog = await _authenticatedApi.getProducts(
        branchId: _controller.branchId,
      );
      final productById = {for (final product in catalog) product.id: product};
      if (!mounted || requestVersion != _recommendationsRequestVersion) return;
      setState(
        () => _recommendedProducts = recommendations.recommendations
            .map((item) => productById[item.productId])
            .whereType<Product>()
            .toList(growable: false),
      );
    } catch (_) {
      if (!mounted || requestVersion != _recommendationsRequestVersion) return;
      setState(() => _recommendedProducts = const []);
    }
  }

  Future<void> _search(String value) async {
    await _controller.search(value);
    if (mounted) await _loadRecommendations();
  }

  Future<void> _retryCatalog() async {
    await _controller.load();
    if (mounted) await _loadRecommendations();
  }

  void _updateFilters({
    String? branchId,
    String? categoryId,
    String? sizeId,
    String? colorId,
    String? seasonId,
    String? collectionId,
  }) {
    unawaited(
      _controller
          .updateFilters(
            branchId: branchId == null
                ? _controller.branchId
                : _emptyAsNull(branchId),
            categoryId: categoryId == null
                ? _controller.categoryId
                : _emptyAsNull(categoryId),
            sizeId: sizeId == null ? _controller.sizeId : _emptyAsNull(sizeId),
            colorId: colorId == null
                ? _controller.colorId
                : _emptyAsNull(colorId),
            seasonId: seasonId == null
                ? _controller.seasonId
                : _emptyAsNull(seasonId),
            collectionId: collectionId == null
                ? _controller.collectionId
                : _emptyAsNull(collectionId),
          )
          .then((_) {
            if (mounted) unawaited(_loadRecommendations());
          }),
    );
  }

  bool get _isCliente =>
      widget.authController?.isAuthenticated == true &&
      widget.authController?.user?.rol.value == 'cliente';

  static String? _emptyAsNull(String? value) =>
      value == null || value.isEmpty ? null : value;
}
