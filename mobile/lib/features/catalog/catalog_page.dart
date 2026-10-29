import 'dart:async';

import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../core/network/api_exception.dart';
import '../../core/storage/session_storage.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_card.dart';
import '../auth/auth_controller.dart';
import '../auth/login_dialog.dart';
import '../cart/cart_api.dart';
import '../chatbot/chatbot_page.dart';
import '../reservations/reservation_models.dart';
import '../../app/theme.dart';
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
  String? _reservationBranchId;
  String? _reservationBranchName;
  String? _reservationTenantName;
  final Set<String> _addingProductIds = {};
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
    _reservationBranchId = widget.reservationArguments?.branchId;
    _reservationBranchName = widget.reservationArguments?.branchName;
    _reservationTenantName = widget.reservationArguments?.tenantName;
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
              const SizedBox(height: 16),
              _shortcuts(),
              const SizedBox(height: 14),
              _tenantSelector(),
              const SizedBox(height: 14),
              _searchField(),
              const SizedBox(height: 10),
              _filterButton(),
              if (_activeFiltersCount > 0) ...[
                const SizedBox(height: 10),
                _activeFilterChips(),
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
        hintText: 'Buscar prendas, estilos...',
        prefixIcon: const Icon(Icons.search, size: 20),
        suffixIcon: _searchController.text.isNotEmpty
            ? IconButton(
                tooltip: 'Limpiar búsqueda',
                icon: const Icon(Icons.clear, size: 18),
                onPressed: () {
                  _searchController.clear();
                  _search('');
                },
              )
            : IconButton(
                tooltip: 'Buscar',
                onPressed: () => _search(_searchController.text),
                icon: const Icon(Icons.arrow_forward, size: 18),
              ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }

  int get _activeFiltersCount {
    var count = 0;
    if (_controller.categoryId != null && _controller.categoryId!.isNotEmpty) count++;
    if (_controller.sizeId != null && _controller.sizeId!.isNotEmpty) count++;
    if (_controller.colorId != null && _controller.colorId!.isNotEmpty) count++;
    if (_controller.seasonId != null && _controller.seasonId!.isNotEmpty) count++;
    if (_controller.collectionId != null && _controller.collectionId!.isNotEmpty) count++;
    return count;
  }

  Widget _filterButton() {
    final activeCount = _activeFiltersCount;
    final hasActive = activeCount > 0;

    return SizedBox(
      width: double.infinity,
      height: 44,
      child: OutlinedButton.icon(
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          backgroundColor: hasActive
              ? Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.35)
              : Theme.of(context).cardColor,
          side: BorderSide(
            color: hasActive
                ? Theme.of(context).colorScheme.primary
                : Colors.grey.shade300,
            width: hasActive ? 1.5 : 1.0,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        onPressed: _openFiltersBottomSheet,
        icon: Badge(
          isLabelVisible: hasActive,
          label: Text('$activeCount'),
          backgroundColor: Theme.of(context).colorScheme.primary,
          child: Icon(
            Icons.tune_rounded,
            size: 20,
            color: hasActive
                ? Theme.of(context).colorScheme.primary
                : Colors.grey.shade700,
          ),
        ),
        label: Text(
          hasActive
              ? 'Filtros aplicados ($activeCount)'
              : 'Filtros',
          style: TextStyle(
            fontSize: 13,
            fontWeight: hasActive ? FontWeight.bold : FontWeight.w500,
            color: hasActive
                ? Theme.of(context).colorScheme.primary
                : Colors.grey.shade700,
          ),
        ),
      ),
    );
  }

  Widget _activeFilterChips() {
    final chips = <Widget>[];

    if (_controller.categoryId != null && _controller.categoryId!.isNotEmpty) {
      final cat = _controller.categories.where((c) => c.id == _controller.categoryId).firstOrNull;
      chips.add(
        InputChip(
          avatar: const Icon(Icons.category_outlined, size: 15),
          label: Text(cat?.name ?? 'Categoría'),
          onDeleted: () => _updateFilters(categoryId: ''),
          deleteIconColor: Colors.grey.shade700,
        ),
      );
    }

    if (_controller.sizeId != null && _controller.sizeId!.isNotEmpty) {
      final size = _controller.sizes.where((s) => s.id == _controller.sizeId).firstOrNull;
      chips.add(
        InputChip(
          avatar: const Icon(Icons.straighten_outlined, size: 15),
          label: Text('Talla: ${size?.name ?? ""}'),
          onDeleted: () => _updateFilters(sizeId: ''),
          deleteIconColor: Colors.grey.shade700,
        ),
      );
    }

    if (_controller.colorId != null && _controller.colorId!.isNotEmpty) {
      final color = _controller.colors.where((c) => c.id == _controller.colorId).firstOrNull;
      chips.add(
        InputChip(
          avatar: const Icon(Icons.palette_outlined, size: 15),
          label: Text('Color: ${color?.name ?? ""}'),
          onDeleted: () => _updateFilters(colorId: ''),
          deleteIconColor: Colors.grey.shade700,
        ),
      );
    }

    if (_controller.seasonId != null && _controller.seasonId!.isNotEmpty) {
      final season = _controller.seasons.where((s) => s.id == _controller.seasonId).firstOrNull;
      chips.add(
        InputChip(
          avatar: const Icon(Icons.wb_sunny_outlined, size: 15),
          label: Text('Temp: ${season?.name ?? ""}'),
          onDeleted: () => _updateFilters(seasonId: ''),
          deleteIconColor: Colors.grey.shade700,
        ),
      );
    }

    if (_controller.collectionId != null && _controller.collectionId!.isNotEmpty) {
      final col = _controller.collections.where((c) => c.id == _controller.collectionId).firstOrNull;
      chips.add(
        InputChip(
          avatar: const Icon(Icons.auto_awesome_motion_outlined, size: 15),
          label: Text('Col: ${col?.name ?? ""}'),
          onDeleted: () => _updateFilters(collectionId: ''),
          deleteIconColor: Colors.grey.shade700,
        ),
      );
    }

    if (chips.isEmpty) return const SizedBox.shrink();

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (final chip in chips)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: chip,
            ),
          ActionChip(
            avatar: const Icon(Icons.delete_sweep_outlined, size: 15, color: Colors.red),
            label: const Text(
              'Limpiar',
              style: TextStyle(color: Colors.red, fontWeight: FontWeight.w600, fontSize: 12),
            ),
            onPressed: () {
              _searchController.clear();
              _controller.clearFilters();
            },
          ),
        ],
      ),
    );
  }

  void _openFiltersBottomSheet() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (bottomSheetContext) {
        return ListenableBuilder(
          listenable: _controller,
          builder: (context, _) {
            final activeCount = _activeFiltersCount;

            return Container(
              constraints: BoxConstraints(
                maxHeight: MediaQuery.of(context).size.height * 0.85,
              ),
              decoration: BoxDecoration(
                color: Theme.of(context).scaffoldBackgroundColor,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: SafeArea(
                top: false,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const SizedBox(height: 12),
                    Center(
                      child: Container(
                        width: 40,
                        height: 4,
                        decoration: BoxDecoration(
                          color: Colors.grey.shade300,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.tune_rounded, size: 22),
                              const SizedBox(width: 8),
                              Text(
                                'Filtros',
                                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              if (activeCount > 0) ...[
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Theme.of(context).colorScheme.primary,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    '$activeCount',
                                    style: TextStyle(
                                      color: Theme.of(context).colorScheme.onPrimary,
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ],
                            ],
                          ),
                          Row(
                            children: [
                              if (activeCount > 0)
                                TextButton(
                                  onPressed: () => _controller.clearFilters(),
                                  child: const Text('Limpiar todo'),
                                ),
                              IconButton(
                                icon: const Icon(Icons.close),
                                tooltip: 'Cerrar',
                                onPressed: () => Navigator.of(bottomSheetContext).pop(),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const Divider(height: 1),
                    Flexible(
                      child: ListView(
                        padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
                        children: [
                          _sheetCategoryFilter(),
                          const SizedBox(height: 18),
                          _sheetSizeFilter(),
                          const SizedBox(height: 18),
                          _sheetColorFilter(),
                          const SizedBox(height: 18),
                          _sheetSeasonFilter(),
                          const SizedBox(height: 18),
                          _sheetCollectionFilter(),
                        ],
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                      child: SizedBox(
                        width: double.infinity,
                        height: 46,
                        child: FilledButton(
                          onPressed: () => Navigator.of(bottomSheetContext).pop(),
                          child: Text(
                            _controller.products.isEmpty
                                ? 'Cerrar'
                                : 'Ver ${_controller.products.length} productos',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _filterSectionHeader({
    required IconData icon,
    required String title,
    String? activeName,
    VoidCallback? onClear,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 18, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 8),
          Text(
            title,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
            ),
          ),
          if (activeName != null && onClear != null) ...[
            const Spacer(),
            InkWell(
              onTap: onClear,
              borderRadius: BorderRadius.circular(4),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                child: Text(
                  'Quitar',
                  style: TextStyle(
                    fontSize: 11,
                    color: Theme.of(context).colorScheme.error,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _filterChoiceChip({
    required String label,
    required bool selected,
    required VoidCallback onSelected,
    Widget? avatar,
  }) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return ChoiceChip(
      avatar: avatar,
      label: Text(label),
      selected: selected,
      onSelected: (_) => onSelected(),
      showCheckmark: false,
      visualDensity: VisualDensity.compact,
      labelStyle: TextStyle(
        fontSize: 13,
        fontWeight: selected ? FontWeight.bold : FontWeight.w500,
        color: selected ? colorScheme.onPrimary : colorScheme.onSurface,
      ),
      selectedColor: colorScheme.primary,
      backgroundColor: theme.brightness == Brightness.dark
          ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.3)
          : colorScheme.surfaceContainerHighest.withValues(alpha: 0.45),
      side: BorderSide(
        color: selected
            ? colorScheme.primary
            : colorScheme.outline.withValues(alpha: 0.25),
        width: selected ? 1.4 : 1.0,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
      ),
    );
  }

  Widget? _colorAvatar(String? hex) {
    if (hex == null || hex.trim().isEmpty) return null;
    var cleaned = hex.trim().replaceAll('#', '');
    if (cleaned.length == 6) {
      cleaned = 'FF$cleaned';
    }
    if (cleaned.length == 8) {
      final value = int.tryParse(cleaned, radix: 16);
      if (value != null) {
        return Container(
          width: 14,
          height: 14,
          decoration: BoxDecoration(
            color: Color(value),
            shape: BoxShape.circle,
            border: Border.all(
              color: Colors.black.withValues(alpha: 0.2),
              width: 1,
            ),
          ),
        );
      }
    }
    return null;
  }

  Widget _sheetCategoryFilter() {
    final categories = _controller.categories;
    final selectedId = _controller.categoryId;
    final activeCategory =
        categories.where((c) => c.id == selectedId).firstOrNull;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _filterSectionHeader(
          icon: Icons.category_outlined,
          title: 'Categoría',
          activeName: activeCategory?.name,
          onClear: selectedId != null && selectedId.isNotEmpty
              ? () => _updateFilters(categoryId: '')
              : null,
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _filterChoiceChip(
              label: 'Todas',
              selected: selectedId == null || selectedId.isEmpty,
              onSelected: () => _updateFilters(categoryId: ''),
            ),
            for (final category in categories)
              _filterChoiceChip(
                label: category.name,
                selected: category.id == selectedId,
                onSelected: () => _updateFilters(
                  categoryId: category.id == selectedId ? '' : category.id,
                ),
              ),
          ],
        ),
      ],
    );
  }

  Widget _sheetSizeFilter() {
    final sizes = _controller.sizes;
    final selectedId = _controller.sizeId;
    final activeSize = sizes.where((s) => s.id == selectedId).firstOrNull;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _filterSectionHeader(
          icon: Icons.straighten_outlined,
          title: 'Talla',
          activeName: activeSize?.name,
          onClear: selectedId != null && selectedId.isNotEmpty
              ? () => _updateFilters(sizeId: '')
              : null,
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _filterChoiceChip(
              label: 'Todas',
              selected: selectedId == null || selectedId.isEmpty,
              onSelected: () => _updateFilters(sizeId: ''),
            ),
            for (final size in sizes)
              _filterChoiceChip(
                label: size.name,
                selected: size.id == selectedId,
                onSelected: () => _updateFilters(
                  sizeId: size.id == selectedId ? '' : size.id,
                ),
              ),
          ],
        ),
      ],
    );
  }

  Widget _sheetColorFilter() {
    final colors = _controller.colors;
    final selectedId = _controller.colorId;
    final activeColor = colors.where((c) => c.id == selectedId).firstOrNull;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _filterSectionHeader(
          icon: Icons.palette_outlined,
          title: 'Color',
          activeName: activeColor?.name,
          onClear: selectedId != null && selectedId.isNotEmpty
              ? () => _updateFilters(colorId: '')
              : null,
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _filterChoiceChip(
              label: 'Todos',
              selected: selectedId == null || selectedId.isEmpty,
              onSelected: () => _updateFilters(colorId: ''),
            ),
            for (final color in colors)
              _filterChoiceChip(
                label: color.name,
                selected: color.id == selectedId,
                avatar: _colorAvatar(color.hexCode),
                onSelected: () => _updateFilters(
                  colorId: color.id == selectedId ? '' : color.id,
                ),
              ),
          ],
        ),
      ],
    );
  }

  Widget _sheetSeasonFilter() {
    final seasons = _controller.seasons;
    final selectedId = _controller.seasonId;
    final activeSeason = seasons.where((s) => s.id == selectedId).firstOrNull;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _filterSectionHeader(
          icon: Icons.wb_sunny_outlined,
          title: 'Temporada',
          activeName: activeSeason?.name,
          onClear: selectedId != null && selectedId.isNotEmpty
              ? () => _updateFilters(seasonId: '')
              : null,
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _filterChoiceChip(
              label: 'Todas',
              selected: selectedId == null || selectedId.isEmpty,
              onSelected: () => _updateFilters(seasonId: ''),
            ),
            for (final season in seasons)
              _filterChoiceChip(
                label: season.name,
                selected: season.id == selectedId,
                onSelected: () => _updateFilters(
                  seasonId: season.id == selectedId ? '' : season.id,
                ),
              ),
          ],
        ),
      ],
    );
  }

  Widget _sheetCollectionFilter() {
    final collections = _controller.collections;
    final selectedId = _controller.collectionId;
    final activeCollection =
        collections.where((c) => c.id == selectedId).firstOrNull;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _filterSectionHeader(
          icon: Icons.auto_awesome_motion_outlined,
          title: 'Colección',
          activeName: activeCollection?.name,
          onClear: selectedId != null && selectedId.isNotEmpty
              ? () => _updateFilters(collectionId: '')
              : null,
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _filterChoiceChip(
              label: 'Todas',
              selected: selectedId == null || selectedId.isEmpty,
              onSelected: () => _updateFilters(collectionId: ''),
            ),
            for (final collection in collections)
              _filterChoiceChip(
                label: collection.name,
                selected: collection.id == selectedId,
                onSelected: () => _updateFilters(
                  collectionId: collection.id == selectedId
                      ? ''
                      : collection.id,
                ),
              ),
          ],
        ),
      ],
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
            variant: AppButtonVariant.outlined,
            icon: const Icon(Icons.event_available_outlined),
            onPressed: () => Navigator.of(context).pushNamed(
              AppRoutes.reservationCreate,
              arguments: ReservationArguments(
                items: List.of(_reservationItems),
                branchId: _reservationBranchId,
                branchName: _reservationBranchName,
                tenantName: _reservationTenantName,
              ),
            ),
            expand: true,
          ),
        ),
      ],
    );
  }

  Widget _tenantSelector() {
    if (_controller.tenants.isEmpty) return const SizedBox.shrink();

    final isAllSelected =
        _controller.tenantId == null || _controller.tenantId!.isEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text(
              'Tiendas y Marcas',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Colors.grey,
              ),
            ),
            const SizedBox(width: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
              decoration: BoxDecoration(
                color: Colors.grey.shade200,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '${_controller.tenants.length}',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey.shade700,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: FilterChip(
                  label: const Text('Todas las tiendas'),
                  selected: isAllSelected,
                  onSelected: (_) => _controller.selectTenant(null),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                    side: BorderSide(
                      color: isAllSelected
                          ? Theme.of(context).colorScheme.primary
                          : Colors.grey.shade300,
                    ),
                  ),
                ),
              ),
              for (final tenant in _controller.tenants)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(tenant.name),
                    selected: _controller.tenantId == tenant.id,
                    onSelected: (_) => _controller.selectTenant(tenant.id),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                      side: BorderSide(
                        color: _controller.tenantId == tenant.id
                            ? Theme.of(context).colorScheme.primary
                            : Colors.grey.shade300,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
        if (_controller.tenantId != null &&
            _controller.tenantId!.isNotEmpty &&
            _controller.filteredBranches.isNotEmpty) ...[
          const SizedBox(height: 12),
          _branchSelector(),
        ],
      ],
    );
  }

  Widget _branchSelector() {
    final branches = _controller.filteredBranches;
    final isAllSelected =
        _controller.branchId == null || _controller.branchId!.isEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text(
              'Sucursales',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Colors.grey,
              ),
            ),
            const SizedBox(width: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
              decoration: BoxDecoration(
                color: Theme.of(context)
                    .colorScheme
                    .primaryContainer
                    .withValues(alpha: 0.35),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '${branches.length}',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: FilterChip(
                  label: const Text('Todas las sucursales'),
                  selected: isAllSelected,
                  onSelected: (_) => _controller.selectBranch(null),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                    side: BorderSide(
                      color: isAllSelected
                          ? Theme.of(context).colorScheme.primary
                          : Colors.grey.shade300,
                    ),
                  ),
                ),
              ),
              for (final branch in branches)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text('${branch.name} (${branch.city})'),
                    selected: _controller.branchId == branch.id,
                    onSelected: (_) => _controller.selectBranch(
                      _controller.branchId == branch.id ? null : branch.id,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                      side: BorderSide(
                        color: _controller.branchId == branch.id
                            ? Theme.of(context).colorScheme.primary
                            : Colors.grey.shade300,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ],
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
    final hasSpecificBranch =
        _controller.branchId != null && _controller.branchId!.isNotEmpty;
    final hasSearchOrFilters =
        _controller.searchQuery.isNotEmpty ||
        (_controller.categoryId != null &&
            _controller.categoryId!.isNotEmpty) ||
        (_controller.sizeId != null && _controller.sizeId!.isNotEmpty) ||
        (_controller.colorId != null && _controller.colorId!.isNotEmpty);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_recommendedProducts.isNotEmpty) ...[
          _carouselContainer(
            header: const AppSectionTitle(
              title: 'Recomendaciones para ti',
              subtitle: 'Prendas sugeridas según tus gustos y visualizaciones.',
            ),
            carousel: _recommendationCarousel(),
          ),
        ],
        if (_controller.products.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 60),
            child: AppEmptyView(
              message: 'No encontramos productos con esos filtros.',
            ),
          )
        else if (hasSpecificBranch ||
            hasSearchOrFilters ||
            _controller.branchSections.isEmpty) ...[
          if (hasSpecificBranch) ...[
            _selectedBranchHeader(),
            const SizedBox(height: 16),
          ],
          _productGrid(),
        ] else ...[
          for (final section in _controller.branchSections)
            _carouselContainer(
              header: _branchSectionHeader(section),
              carousel: _branchSectionCarousel(section),
            ),
        ],
      ],
    );
  }

  Widget _selectedBranchHeader() {
    final branch = _controller.branches
        .where((b) => b.id == _controller.branchId)
        .firstOrNull;
    final tenant = _controller.tenants
        .where((t) => t.id == branch?.tenantId)
        .firstOrNull;
    final displayName = branch != null
        ? '${tenant?.name ?? "Tienda"} — ${branch.name} (${branch.city})'
        : 'Sucursal seleccionada';

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(
          context,
        ).colorScheme.primaryContainer.withValues(alpha: 0.25),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: Theme.of(
            context,
          ).colorScheme.primary.withValues(alpha: 0.3),
        ),
      ),
      child: Row(
        children: [
          Icon(Icons.storefront, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Sucursal seleccionada',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: Colors.grey,
                  ),
                ),
                Text(
                  displayName,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, size: 18),
            tooltip: 'Volver a ver todas las sucursales',
            onPressed: () => _controller.selectBranch(null),
          ),
        ],
      ),
    );
  }

  Widget _branchSectionHeader(CatalogBranchSection section) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  '🏪 ${section.tenantName}',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: Colors.grey.shade800,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '🏬 ${section.tenantName} — ${section.branchName} (${section.cityName})',
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
        TextButton(
          onPressed: () => _controller.selectBranch(section.branchId),
          child: const Text(
            'Ver sucursal',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
          ),
        ),
      ],
    );
  }

  Widget _carouselContainer({
    required Widget header,
    required Widget carousel,
  }) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark
            ? theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.25)
            : AppColors.muted,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? AppDarkColors.border : AppColors.border,
          width: 1.0,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          header,
          const SizedBox(height: 12),
          carousel,
        ],
      ),
    );
  }

  Widget _branchSectionCarousel(CatalogBranchSection section) {
    return SizedBox(
      height: 350,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: section.products.length,
        separatorBuilder: (_, _) => const SizedBox(width: 14),
        itemBuilder: (context, index) => SizedBox(
          width: 195,
          child: _productCard(
            section.products[index],
            preferredBranchId: section.branchId,
          ),
        ),
      ),
    );
  }

  Widget _recommendationCarousel() {
    return SizedBox(
      height: 350,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: _recommendedProducts.length,
        separatorBuilder: (_, _) => const SizedBox(width: 14),
        itemBuilder: (context, index) => SizedBox(
          width: 195,
          child: _productCard(_recommendedProducts[index]),
        ),
      ),
    );
  }

  Widget _productGrid() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
        maxCrossAxisExtent: 240,
        mainAxisSpacing: 14,
        crossAxisSpacing: 14,
        childAspectRatio: 0.58,
      ),
      itemCount: _controller.products.length,
      itemBuilder: (context, index) => _productCard(
        _controller.products[index],
        preferredBranchId: _controller.branchId,
      ),
    );
  }

  Widget _productCard(
    Product product, {
    String? preferredBranchId,
  }) {
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

    final tenant = _controller.tenants
        .where((t) => t.id == product.tenantId)
        .firstOrNull;
    final tenantName = tenant?.name;

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
      tenantName: tenantName,
      isAddingToCart: _addingProductIds.contains(product.id),
      onTap: () => _openProduct(
        product,
        preferredBranchId: preferredBranchId,
      ),
      onAddToCart: () => _addVariantToCart(
        product,
        preferredBranchId: preferredBranchId,
      ),
      onReserve: () => _addVariantToReservation(
        product,
        preferredBranchId: preferredBranchId,
      ),
    );
  }

  Branch? _resolveBranchForProduct(
    Product product,
    String? preferredBranchId,
  ) {
    if (preferredBranchId != null) {
      final match = _controller.branches
          .where((b) => b.id == preferredBranchId)
          .firstOrNull;
      if (match != null) return match;
    }
    if (_controller.branchId != null) {
      final match = _controller.branches
          .where((b) => b.id == _controller.branchId)
          .firstOrNull;
      if (match != null) return match;
    }
    if (product.tenantId != null) {
      final match = _controller.branches
          .where((b) => b.tenantId == product.tenantId)
          .firstOrNull;
      if (match != null) return match;
    }
    return _controller.branches.firstOrNull;
  }

  Future<void> _addVariantToCart(
    Product product, {
    String? preferredBranchId,
  }) async {
    final variants = product.variants ?? const [];
    final primaryVariant = variants.isEmpty ? null : variants.first;
    if (primaryVariant == null) {
      _openProduct(product, preferredBranchId: preferredBranchId);
      return;
    }

    final authController = widget.authController;
    if (authController == null || !authController.isAuthenticated) {
      final loggedIn = await LoginDialog.show(
        context: context,
        controller: authController ?? AuthController(),
      );
      if (!mounted || loggedIn != true) return;
    }

    final targetBranch = _resolveBranchForProduct(
      product,
      preferredBranchId,
    );
    final tenant = _controller.tenants
        .where(
          (t) =>
              t.id == product.tenantId ||
              t.id == targetBranch?.tenantId,
        )
        .firstOrNull;
    final tenantName = tenant?.name ?? 'Tienda';
    final targetBranchId = targetBranch?.id;
    final targetBranchName = targetBranch != null
        ? '${targetBranch.name} (${targetBranch.city})'
        : 'Sucursal';

    final sessionStorage = const SessionStorage();
    final cartContext = await sessionStorage.readCartContext();

    final api = CartApi(
      tokenProvider: () => widget.authController?.accessToken,
      onUnauthorized: widget.authController?.handleUnauthorized,
    );

    try {
      if (!mounted) return;
      // One cart per company: the backend rejects another company's item with a clear message.

      setState(() => _addingProductIds.add(product.id));
      final res = await api.addItem(
        variantId: primaryVariant.id,
        quantity: 1,
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
          res.message,
          tone: AppSnackBarTone.success,
        );
      }
    } catch (e) {
      if (mounted) {
        AppSnackBar.show(
          context,
          e is ApiException ? e.message : 'No se pudo agregar al carrito.',
          tone: AppSnackBarTone.error,
        );
      }
    } finally {
      if (mounted) {
        setState(() => _addingProductIds.remove(product.id));
      }
    }
  }

  Future<void> _addVariantToReservation(
    Product product, {
    String? preferredBranchId,
  }) async {
    final variants = product.variants ?? const [];
    final primaryVariant = variants.isEmpty ? null : variants.first;
    if (primaryVariant == null) {
      _openProduct(product, preferredBranchId: preferredBranchId);
      return;
    }

    final targetBranch = _resolveBranchForProduct(
      product,
      preferredBranchId,
    );
    final tenant = _controller.tenants
        .where(
          (t) =>
              t.id == product.tenantId ||
              t.id == targetBranch?.tenantId,
        )
        .firstOrNull;
    final tenantName = tenant?.name ?? 'Tienda';
    final targetBranchId = targetBranch?.id;
    final targetBranchName = targetBranch != null
        ? '${targetBranch.name} (${targetBranch.city})'
        : 'Sucursal';

    if (_reservationItems.isNotEmpty &&
        _reservationBranchId != null &&
        targetBranchId != null &&
        _reservationBranchId != targetBranchId) {
      final currentFullName =
          _reservationTenantName != null &&
                  _reservationTenantName!.isNotEmpty
              ? '$_reservationTenantName — $_reservationBranchName'
              : (_reservationBranchName ?? 'otra sucursal');

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

      if (!mounted || confirm != true) return;
      _reservationItems.clear();
    }

    final selectedItem = ReservationDraftItem(
      variantId: primaryVariant.id,
      quantity: 1,
      productName: product.name,
      variantSku:
          primaryVariant.sku.isEmpty ? product.sku : primaryVariant.sku,
      imageUrl: primaryVariant.imageUrl ?? product.imageUrl,
    );

    final existingIndex = _reservationItems.indexWhere(
      (item) => item.variantId == selectedItem.variantId,
    );
    if (existingIndex == -1) {
      _reservationItems.add(selectedItem);
    } else {
      final existing = _reservationItems[existingIndex];
      _reservationItems[existingIndex] = ReservationDraftItem(
        variantId: existing.variantId,
        quantity: existing.quantity + 1,
        productName: selectedItem.productName ?? existing.productName,
        variantSku: selectedItem.variantSku ?? existing.variantSku,
        imageUrl: selectedItem.imageUrl ?? existing.imageUrl,
      );
    }

    _reservationBranchId = targetBranchId;
    _reservationBranchName = targetBranchName;
    _reservationTenantName = tenantName;

    setState(() {});
    AppSnackBar.show(
      context,
      'Prenda agregada a la reserva.',
      tone: AppSnackBarTone.success,
    );
  }

  Future<void> _openProduct(
    Product product, {
    String? preferredBranchId,
  }) async {
    unawaited(_recordProductView(product));
    final result = await Navigator.of(context).pushNamed(
      AppRoutes.productDetail,
      arguments: ProductDetailArguments(
        product: product,
        sizes: _controller.sizes,
        colors: _controller.colors,
        branches: _controller.branches,
        tenants: _controller.tenants,
        branchId: preferredBranchId ?? _controller.branchId,
        reservationArguments: ReservationArguments(
          items: List.of(_reservationItems),
          branchId: _reservationBranchId,
          branchName: _reservationBranchName,
          tenantName: _reservationTenantName,
        ),
      ),
    );
    if (!mounted || result is! ReservationArguments) return;

    setState(() {
      _reservationItems = List.of(result.items);
      _reservationBranchId = result.branchId;
      _reservationBranchName = result.branchName;
      _reservationTenantName = result.tenantName;
    });
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
