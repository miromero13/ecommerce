import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/filter_chip.dart';
import '../../shared/widgets/product_card.dart';
import 'catalog_controller.dart';
import 'catalog_models.dart';
import 'product_detail_page.dart';

class CatalogPage extends StatefulWidget {
  const CatalogPage({super.key, this.controller});

  final CatalogController? controller;

  @override
  State<CatalogPage> createState() => _CatalogPageState();
}

class _CatalogPageState extends State<CatalogPage> {
  late final CatalogController _controller;
  late final bool _ownsController;
  late final TextEditingController _searchController;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller = widget.controller ?? CatalogController();
    _searchController = TextEditingController();
    if (_controller.status == CatalogStatus.idle) {
      _controller.load();
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
      builder: (context, _) => ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const AppSectionTitle(
            title: 'Catálogo público',
            subtitle: 'Explora las prendas disponibles en FashionStore.',
          ),
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
    );
  }

  Widget _searchField() {
    return TextField(
      controller: _searchController,
      textInputAction: TextInputAction.search,
      onSubmitted: _controller.search,
      decoration: InputDecoration(
        hintText: 'Buscar productos',
        prefixIcon: const Icon(Icons.search),
        suffixIcon: IconButton(
          tooltip: 'Buscar',
          onPressed: () => _controller.search(_searchController.text),
          icon: const Icon(Icons.arrow_forward),
        ),
      ),
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
          onRetry: _controller.load,
        ),
      ),
      CatalogStatus.ready when _controller.products.isEmpty => const Padding(
        padding: EdgeInsets.symmetric(vertical: 80),
        child: AppEmptyView(
          message: 'No encontramos productos con esos filtros.',
        ),
      ),
      CatalogStatus.ready => _productGrid(),
    };
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
      itemBuilder: (context, index) {
        final product = _controller.products[index];
        final imageUrls = (product.variants ?? const <ProductVariant>[])
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
          price: product.price,
          imageUrl: imageUrls.isEmpty ? product.imageUrl : null,
          variantImageUrls: imageUrls,
          badge: badge,
          onTap: () => Navigator.of(context).pushNamed(
            AppRoutes.productDetail,
            arguments: ProductDetailArguments(
              product: product,
              sizes: _controller.sizes,
              colors: _controller.colors,
              branches: _controller.branches,
              branchId: _controller.branchId,
            ),
          ),
        );
      },
    );
  }

  void _updateFilters({
    String? branchId,
    String? categoryId,
    String? sizeId,
    String? colorId,
    String? seasonId,
    String? collectionId,
  }) {
    _controller.updateFilters(
      branchId: branchId == null
          ? _controller.branchId
          : _emptyAsNull(branchId),
      categoryId: categoryId == null
          ? _controller.categoryId
          : _emptyAsNull(categoryId),
      sizeId: sizeId == null ? _controller.sizeId : _emptyAsNull(sizeId),
      colorId: colorId == null ? _controller.colorId : _emptyAsNull(colorId),
      seasonId: seasonId == null
          ? _controller.seasonId
          : _emptyAsNull(seasonId),
      collectionId: collectionId == null
          ? _controller.collectionId
          : _emptyAsNull(collectionId),
    );
  }

  static String? _emptyAsNull(String? value) =>
      value == null || value.isEmpty ? null : value;
}
