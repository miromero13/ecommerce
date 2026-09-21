import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/product_image.dart';
import '../../shared/widgets/product_price.dart';
import '../../shared/widgets/quantity_selector.dart';
import '../auth/auth_controller.dart';
import '../auth/login_dialog.dart';
import '../../app/routes.dart';
import 'cart_api.dart';
import 'cart_controller.dart';
import 'cart_models.dart';

class CartPage extends StatefulWidget {
  const CartPage({super.key, required this.authController, this.controller});

  final AuthController authController;
  final CartController? controller;

  @override
  State<CartPage> createState() => _CartPageState();
}

class _CartPageState extends State<CartPage> {
  late final CartController _controller;
  late final bool _ownsController;
  String? _loadedToken;
  final _couponController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller =
        widget.controller ??
        CartController(
          api: CartApi(
            tokenProvider: () => widget.authController.accessToken,
            onUnauthorized: widget.authController.handleUnauthorized,
          ),
        );
    widget.authController.addListener(_handleAuthChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) => _handleAuthChanged());
  }

  @override
  void dispose() {
    widget.authController.removeListener(_handleAuthChanged);
    if (_ownsController) _controller.dispose();
    _couponController.dispose();
    super.dispose();
  }

  void _handleAuthChanged() {
    if (!mounted) return;
    if (!widget.authController.isAuthenticated) {
      _loadedToken = null;
      return;
    }

    final token = widget.authController.accessToken;
    if (token == null || token == _loadedToken) return;
    _loadedToken = token;
    _controller.load();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.authController,
      builder: (context, _) {
        if (widget.authController.status == AuthStatus.loading) {
          return const AppLoading(message: 'Validando sesión...');
        }
        if (widget.authController.status == AuthStatus.error) {
          return AppErrorView(
            message:
                widget.authController.errorMessage ??
                'No se pudo validar la sesión.',
            onRetry: widget.authController.restoreSession,
          );
        }
        if (!widget.authController.isAuthenticated) {
          return AppEmptyView(
            title: 'Carrito privado',
            message: 'Inicia sesión para consultar tu carrito.',
            actionLabel: 'Iniciar sesión',
            onAction: () => LoginDialog.show(
              context: context,
              controller: widget.authController,
            ),
          );
        }

        return ListenableBuilder(
          listenable: _controller,
          builder: (context, _) => _buildCart(context),
        );
      },
    );
  }

  Widget _buildCart(BuildContext context) {
    final cart = _controller.cart;
    if (cart == null && _controller.status == CartControllerStatus.loading) {
      return const AppLoading(message: 'Cargando carrito...');
    }
    if (cart == null && _controller.status == CartControllerStatus.error) {
      return AppErrorView(
        message: _controller.errorMessage ?? 'No se pudo cargar el carrito.',
        onRetry: _controller.load,
      );
    }
    if (cart == null) {
      return const AppLoading(message: 'Cargando carrito...');
    }
    if (cart.items.isEmpty) return _emptyCart(context);

    return RefreshIndicator(
      onRefresh: _controller.load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          if (_controller.status == CartControllerStatus.loading)
            const LinearProgressIndicator(minHeight: 2),
          AppSectionTitle(
            title: 'Tu carrito',
            subtitle: _itemCountLabel(cart.itemCount),
          ),
          const SizedBox(height: 16),
          for (final item in cart.items) ...[
            _CartItemCard(
              item: item,
              enabled: _controller.status != CartControllerStatus.loading,
              onQuantityChanged: (quantity) => _updateQuantity(item, quantity),
              onRemove: () => _removeItem(item),
            ),
            const SizedBox(height: 12),
          ],
           const SizedBox(height: 4),
           _SummaryCard(cart: cart),
           const SizedBox(height: 12),
           _CouponCard(
             cart: cart,
             controller: _couponController,
             onApply: () => _runMutation(() => _controller.applyCoupon(_couponController.text)),
             onRemove: () => _runMutation(_controller.removeCoupon),
           ),
           const SizedBox(height: 16),
           AppButton(
             label: 'Continuar',
             icon: Icon(Icons.arrow_forward),
             onPressed: () => Navigator.of(context).pushNamed(AppRoutes.checkout),
             expand: true,
           ),
        ],
      ),
    );
  }

  Widget _emptyCart(BuildContext context) {
    return AppEmptyView(
      title: 'Tu carrito está vacío',
      message: 'Explora el catálogo y agrega prendas para continuar.',
      actionLabel: 'Ver catálogo',
      onAction: () => Navigator.of(context).pushReplacementNamed('/'),
    );
  }

  String _itemCountLabel(int count) {
    return count == 1
        ? '1 producto seleccionado'
        : '$count productos seleccionados';
  }

  Future<void> _updateQuantity(CartItem item, int quantity) {
    return _runMutation(
      () => _controller.updateItem(itemId: item.id, quantity: quantity),
    );
  }

  Future<void> _removeItem(CartItem item) {
    return _runMutation(() => _controller.removeItem(itemId: item.id));
  }

  Future<void> _runMutation(Future<void> Function() mutation) async {
    await mutation();
    if (!mounted) return;
    final isError = _controller.status == CartControllerStatus.error;
    final message = isError
        ? _controller.errorMessage
        : _controller.feedbackMessage;
    if (message != null) {
      AppSnackBar.show(
        context,
        message,
        tone: isError ? AppSnackBarTone.error : AppSnackBarTone.success,
      );
    }
  }
}

class _CartItemCard extends StatelessWidget {
  const _CartItemCard({
    required this.item,
    required this.enabled,
    required this.onQuantityChanged,
    required this.onRemove,
  });

  final CartItem item;
  final bool enabled;
  final ValueChanged<int> onQuantityChanged;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    final variant = [
      if (item.variantSku.trim().isNotEmpty) item.variantSku,
      if (item.sizeName != null) 'Talla ${item.sizeName}',
      if (item.colorName != null) 'Color ${item.colorName}',
    ].join(' · ');

    return AbsorbPointer(
      absorbing: !enabled,
      child: AppCard(
        child: Column(
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 88,
                  height: 112,
                  child: ProductImage(imageUrl: item.imageUrl),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.productName,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      if (variant.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          variant,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                      const SizedBox(height: 8),
                       ProductPrice(
                         price: item.lineTotal,
                         originalPrice: item.originalUnitPrice == null
                             ? null
                             : item.originalUnitPrice! * item.quantity,
                       ),
                      Text(
                        'Bs ${item.unitPrice.toStringAsFixed(2)} c/u',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.slate600,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: onRemove,
                  tooltip: 'Eliminar producto',
                  icon: const Icon(Icons.delete_outline),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Cantidad', style: Theme.of(context).textTheme.bodyMedium),
                QuantitySelector(
                  value: item.quantity,
                  max: item.quantity >= 99 ? item.quantity + 1 : 99,
                  onChanged: onQuantityChanged,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.cart});

  final Cart cart;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        children: [
          _SummaryRow(label: 'Subtotal', amount: cart.subtotal),
          const SizedBox(height: 8),
          _SummaryRow(
            label: 'Descuento',
            amount: cart.discountAmount,
            color: AppColors.success,
            prefix: '- ',
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Divider(),
          ),
          _SummaryRow(
            label: 'Total',
            amount: cart.totalAmount,
            emphasized: true,
          ),
        ],
      ),
    );
  }
}

class _CouponCard extends StatelessWidget {
  const _CouponCard({required this.cart, required this.controller, required this.onApply, required this.onRemove});

  final Cart cart;
  final TextEditingController controller;
  final VoidCallback onApply;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: cart.promotionCode != null
          ? Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text('Cupón: ${cart.promotionCode}'),
              TextButton(onPressed: onRemove, child: const Text('Retirar')),
            ])
          : Row(children: [
              Expanded(child: TextField(controller: controller, textCapitalization: TextCapitalization.characters, decoration: const InputDecoration(labelText: 'Código promocional'))),
              const SizedBox(width: 10),
              TextButton(onPressed: onApply, child: const Text('Aplicar')),
            ]),
    );
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow({
    required this.label,
    required this.amount,
    this.color,
    this.emphasized = false,
    this.prefix = '',
  });

  final String label;
  final double amount;
  final Color? color;
  final bool emphasized;
  final String prefix;

  @override
  Widget build(BuildContext context) {
    final style = Theme.of(context).textTheme.titleMedium?.copyWith(
      fontWeight: emphasized ? FontWeight.w700 : FontWeight.w500,
      color: color,
    );
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: style),
        Text('${prefix}Bs ${amount.toStringAsFixed(2)}', style: style),
      ],
    );
  }
}
