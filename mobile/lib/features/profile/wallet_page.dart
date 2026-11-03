import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../shared/widgets/app_badge.dart';
import '../../shared/widgets/app_bottom_sheet.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_divider.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/app_text_field.dart';
import '../auth/auth_controller.dart';

/// CU17, CU18 & CU19: Hub Unificado de Billetera Digital y Fidelización reutilizando widgets compartidos.
class WalletPage extends StatefulWidget {
  const WalletPage({super.key, required this.authController});

  final AuthController authController;

  @override
  State<WalletPage> createState() => _WalletPageState();
}

class _WalletPageState extends State<WalletPage> with SingleTickerProviderStateMixin {
  late final ApiClient _client = ApiClient(
    tokenProvider: () => widget.authController.accessToken,
    onUnauthorized: widget.authController.handleUnauthorized,
  );

  late final TabController _tabController = TabController(length: 2, vsync: this);

  final _codeController = TextEditingController();
  final _recipientNameController = TextEditingController();
  final _recipientEmailController = TextEditingController();
  final _customGiftMessageController = TextEditingController();
  final _customGiftAmountController = TextEditingController();

  double? _balance;
  String _currency = 'BOB';
  List<Map<String, dynamic>>? _transactions;
  List<Map<String, dynamic>>? _loyaltyBalances;
  List<Map<String, dynamic>>? _loyaltyMovements;

  bool _isRedeeming = false;
  bool _isConverting = false;
  bool _isPurchasingGift = false;
  final List<int> _giftPresets = [20, 50, 100];
  int _selectedGiftAmount = 50;
  bool _isCustomGift = false;

  static const _conceptLabels = {
    'gift_card_redeem': 'Canje Gift Card',
    'points_conversion': 'Conversión de Puntos',
    'order_payment': 'Pago de pedido',
    'sale_payment': 'Pago en tienda',
    'rma_refund': 'Reembolso RMA',
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _codeController.dispose();
    _recipientNameController.dispose();
    _recipientEmailController.dispose();
    _customGiftMessageController.dispose();
    _customGiftAmountController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final results = await Future.wait([
        _client.get<Map<String, dynamic>>('wallet/balance', parser: (d) => Map<String, dynamic>.from(d as Map)),
        _client.get<List<dynamic>>('wallet/transactions', parser: (d) => d as List),
        _client.get<List<dynamic>>('loyalty/balance', parser: (d) => d as List),
        _client.get<List<dynamic>>('loyalty/transactions', parser: (d) => d as List),
      ]);

      if (mounted) {
        setState(() {
          _balance = (results[0].data?['balance'] as num?)?.toDouble() ?? 0.0;
          _currency = results[0].data?['currency']?.toString() ?? 'BOB';
          _transactions = (results[1].data ?? const []).map((r) => Map<String, dynamic>.from(r as Map)).toList();
          _loyaltyBalances = (results[2].data ?? const []).map((r) => Map<String, dynamic>.from(r as Map)).toList();
          _loyaltyMovements = (results[3].data ?? const []).map((r) => Map<String, dynamic>.from(r as Map)).toList();
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _balance = 0.0;
          _transactions = const [];
          _loyaltyBalances = const [];
          _loyaltyMovements = const [];
        });
      }
    }
  }

  Future<void> _redeemGiftCard() async {
    final code = _codeController.text.trim();
    if (code.isEmpty) {
      AppSnackBar.show(context, 'Ingresa el código de la tarjeta de regalo', tone: AppSnackBarTone.error);
      return;
    }

    setState(() => _isRedeeming = true);
    try {
      final res = await _client.post<Map<String, dynamic>>(
        'wallet/redeem-gift-card',
        data: {'card_code': code},
        parser: (data) => Map<String, dynamic>.from(data as Map),
      );
      if (!mounted) return;
      AppSnackBar.show(context, res.message ?? 'Gift Card canjeada exitosamente.', tone: AppSnackBarTone.success);
      _codeController.clear();
      _load();
    } catch (error) {
      if (!mounted) return;
      AppSnackBar.show(
        context,
        error is ApiException ? error.message : 'Código inválido o ya canjeado',
        tone: AppSnackBarTone.error,
      );
    } finally {
      if (mounted) setState(() => _isRedeeming = false);
    }
  }

  Future<void> _convertPoints(Map<String, dynamic> row) async {
    final rawBalance = (row['points_balance'] as num?)?.toInt() ?? 0;
    final convertible = (rawBalance ~/ 100) * 100;
    if (convertible < 100) return;

    setState(() => _isConverting = true);
    try {
      final res = await _client.post<Map<String, dynamic>>(
        'wallet/convert-points',
        data: {'tenant_id': row['tenant_id'], 'points': convertible},
        parser: (data) => Map<String, dynamic>.from(data as Map),
      );
      if (!mounted) return;
      AppSnackBar.show(context, res.message ?? '¡Puntos convertidos a saldo!', tone: AppSnackBarTone.success);
      _load();
    } catch (error) {
      if (!mounted) return;
      AppSnackBar.show(
        context,
        error is ApiException ? error.message : 'No se pudieron convertir los puntos.',
        tone: AppSnackBarTone.error,
      );
    } finally {
      if (mounted) setState(() => _isConverting = false);
    }
  }

  Future<void> _purchaseGiftCard(StateSetter setModalState, BuildContext modalContext) async {
    final amount = _isCustomGift
        ? (double.tryParse(_customGiftAmountController.text.trim()) ?? 0.0)
        : _selectedGiftAmount.toDouble();
    final name = _recipientNameController.text.trim();
    final email = _recipientEmailController.text.trim();
    final msg = _customGiftMessageController.text.trim();

    if (amount < 10) {
      AppSnackBar.show(context, 'El importe mínimo es \$10.00 BOB', tone: AppSnackBarTone.error);
      return;
    }
    if (name.isEmpty || !email.contains('@')) {
      AppSnackBar.show(context, 'Completa los datos válidos del destinatario', tone: AppSnackBarTone.error);
      return;
    }

    setModalState(() => _isPurchasingGift = true);
    try {
      final res = await _client.post<Map<String, dynamic>>(
        'gift-cards/purchase',
        data: {
          'amount': amount,
          'recipient_name': name,
          'recipient_email': email,
          if (msg.isNotEmpty) 'custom_message': msg,
          'payment_method': 'stripe',
        },
        parser: (data) => Map<String, dynamic>.from(data as Map),
      );
      if (!mounted) return;
      Navigator.of(modalContext).pop();
      AppSnackBar.show(context, res.message ?? 'Tarjeta de regalo adquirida y enviada por correo', tone: AppSnackBarTone.success);
      _recipientNameController.clear();
      _recipientEmailController.clear();
      _customGiftMessageController.clear();
      _customGiftAmountController.clear();
      _load();
    } catch (error) {
      if (!mounted) return;
      AppSnackBar.show(
        context,
        error is ApiException ? error.message : 'Error al comprar Gift Card',
        tone: AppSnackBarTone.error,
      );
    } finally {
      setModalState(() => _isPurchasingGift = false);
    }
  }

  void _showBuyGiftCardModal() {
    AppBottomSheet.show<void>(
      context: context,
      title: 'Comprar Tarjeta de Regalo',
      isScrollControlled: true,
      child: StatefulBuilder(
        builder: (context, setModalState) {
          return SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'El destinatario recibirá un correo con el código y QR para canjear en su Billetera.',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
                const SizedBox(height: 16),
                const Text('Monto del obsequio', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    for (final p in _giftPresets)
                      Expanded(
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 4),
                          child: AppButton(
                            label: '\$$p',
                            variant: (!_isCustomGift && _selectedGiftAmount == p)
                                ? AppButtonVariant.primary
                                : AppButtonVariant.outlined,
                            onPressed: () => setModalState(() {
                              _isCustomGift = false;
                              _selectedGiftAmount = p;
                            }),
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 6),
                AppButton(
                  label: _isCustomGift ? 'Usar monto predefinido' : '+ Monto personalizado',
                  variant: AppButtonVariant.text,
                  onPressed: () => setModalState(() => _isCustomGift = !_isCustomGift),
                ),
                if (_isCustomGift) ...[
                  const SizedBox(height: 6),
                  AppTextField(
                    controller: _customGiftAmountController,
                    label: 'Monto en BOB (mínimo 10.00)',
                    keyboardType: TextInputType.number,
                  ),
                ],
                const SizedBox(height: 12),
                AppTextField(controller: _recipientNameController, label: 'Nombre del destinatario'),
                const SizedBox(height: 10),
                AppTextField(
                  controller: _recipientEmailController,
                  label: 'Correo electrónico',
                  keyboardType: TextInputType.emailAddress,
                ),
                const SizedBox(height: 10),
                AppTextField(
                  controller: _customGiftMessageController,
                  label: 'Mensaje personal o dedicatoria (opcional)',
                  maxLines: 2,
                ),
                const SizedBox(height: 16),
                AppButton(
                  label: _isPurchasingGift ? 'Procesando compra...' : 'Confirmar Compra',
                  icon: const Icon(Icons.card_giftcard),
                  isLoading: _isPurchasingGift,
                  expand: true,
                  onPressed: _isPurchasingGift ? null : () => _purchaseGiftCard(setModalState, context),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showPointsHistoryModal() {
    final movements = _loyaltyMovements ?? const [];
    AppBottomSheet.show<void>(
      context: context,
      title: 'Historial de Puntos',
      isScrollControlled: true,
      child: movements.isEmpty
          ? const AppEmptyView(title: 'Sin movimientos', message: 'Aún no hay puntos registrados.')
          : SizedBox(
              height: 380,
              child: ListView.separated(
                itemCount: movements.length,
                separatorBuilder: (_, __) => const AppDivider(),
                itemBuilder: (_, index) {
                  final m = movements[index];
                  final isRedeem = m['type'] == 'redeem';
                  return ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: CircleAvatar(
                      backgroundColor: isRedeem ? Colors.red.shade100 : Colors.green.shade100,
                      child: Icon(
                        isRedeem ? Icons.remove : Icons.add,
                        color: isRedeem ? Colors.red.shade800 : Colors.green.shade800,
                        size: 18,
                      ),
                    ),
                    title: Text(m['tenant_name']?.toString() ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text('${isRedeem ? 'Canjeados' : 'Ganados'} · ${m['created_at']}'),
                    trailing: Text(
                      '${isRedeem ? '-' : '+'}${m['points']} pts',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: isRedeem ? Colors.red.shade700 : Colors.green.shade700,
                      ),
                    ),
                  );
                },
              ),
            ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final balance = _balance;

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const AppSectionTitle(
            title: 'Mi Billetera Digital',
            subtitle: 'Saldo disponible y puntos de fidelidad unificados.',
          ),
          const SizedBox(height: 16),

          // Tarjeta Principal en BOB
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF0F172A), Color(0xFF1E1B4B), Color(0xFF312E81)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: Colors.indigo.withOpacity(0.3),
                  blurRadius: 12,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'FASHION STORE WALLET',
                      style: TextStyle(color: Colors.white70, fontSize: 11, letterSpacing: 1.5, fontWeight: FontWeight.bold),
                    ),
                    const AppBadge(
                      label: 'Activa',
                      tone: AppBadgeTone.success,
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                const Text('Saldo total disponible', style: TextStyle(color: Colors.white70, fontSize: 12)),
                const SizedBox(height: 4),
                Text(
                  balance == null ? 'Cargando...' : '\$${balance.toStringAsFixed(2)} $_currency',
                  style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 14),
                const Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Válida para compras en cualquier marca', style: TextStyle(color: Colors.white60, fontSize: 11)),
                    Icon(Icons.contactless_outlined, color: Colors.white70, size: 20),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Canje Rápido de Gift Card + Botón Modal de Compra reutilizando AppCard
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.card_giftcard, color: Colors.indigo, size: 20),
                    const SizedBox(width: 8),
                    Text('¿Tienes una Gift Card?', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: AppTextField(
                        controller: _codeController,
                        label: 'Código (ej. GIFT-2026-X89Q)',
                      ),
                    ),
                    const SizedBox(width: 8),
                    AppButton(
                      label: _isRedeeming ? '...' : 'Canjear',
                      isLoading: _isRedeeming,
                      onPressed: _isRedeeming ? null : _redeemGiftCard,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                const AppDivider(),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('¿Quieres regalar un voucher?', style: TextStyle(fontSize: 12, color: Colors.grey)),
                    AppButton(
                      label: 'Comprar Gift Card →',
                      variant: AppButtonVariant.text,
                      icon: const Icon(Icons.add, size: 16),
                      onPressed: _showBuyGiftCardModal,
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // Pestañas del Hub (Solo 2 pestañas fijas)
          TabBar(
            controller: _tabController,
            labelColor: Theme.of(context).colorScheme.primary,
            unselectedLabelColor: Colors.grey,
            indicatorColor: Theme.of(context).colorScheme.primary,
            tabs: const [
              Tab(text: '🪙 Movimientos'),
              Tab(text: '⭐ Mis Puntos'),
            ],
          ),
          const SizedBox(height: 16),

          // Contenido de las 2 pestañas
          AnimatedBuilder(
            animation: _tabController,
            builder: (context, _) {
              return switch (_tabController.index) {
                0 => _buildMovementsTab(),
                _ => _buildPointsTab(),
              };
            },
          ),
        ],
      ),
    );
  }

  Widget _buildMovementsTab() {
    final txs = _transactions;
    if (txs == null) return const AppLoading();
    if (txs.isEmpty) {
      return const AppEmptyView(title: 'Sin movimientos', message: 'Tus transacciones de saldo aparecerán aquí.');
    }
    return Column(
      children: [
        for (final tx in txs) ...[
          AppCard(
            child: ListTile(
              contentPadding: EdgeInsets.zero,
              leading: CircleAvatar(
                backgroundColor: tx['type'] == 'credit' ? Colors.green.shade100 : Colors.red.shade100,
                child: Icon(
                  tx['type'] == 'credit' ? Icons.arrow_downward : Icons.arrow_upward,
                  color: tx['type'] == 'credit' ? Colors.green.shade800 : Colors.red.shade800,
                  size: 18,
                ),
              ),
              title: Text(_conceptLabels[tx['concept']] ?? tx['concept']?.toString() ?? '', style: const TextStyle(fontWeight: FontWeight.w600)),
              subtitle: Text(tx['description']?.toString() ?? ''),
              trailing: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${tx['type'] == 'credit' ? '+' : '-'}\$${tx['amount']}',
                    style: TextStyle(
                      color: tx['type'] == 'credit' ? Colors.green.shade700 : Colors.red.shade700,
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                  Text('Saldo: \$${tx['balance_after']}', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ],
    );
  }

  Widget _buildPointsTab() {
    final balances = _loyaltyBalances;
    if (balances == null) return const AppLoading();
    if (balances.isEmpty) {
      return const AppEmptyView(
        title: 'Aún no tienes puntos',
        message: 'Ganarás puntos por compras en cada empresa para convertirlos en saldo de billetera.',
      );
    }
    return Column(
      children: [
        for (final row in balances) ...[
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(row['tenant_name']?.toString() ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    AppBadge(
                      label: row['tier']?.toString() ?? 'Bronce',
                      tone: AppBadgeTone.warning,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  '${row['points_balance']} puntos',
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900),
                ),
                Text(
                  'Equivalen a \$${row['balance_value']} BOB · ${row['lifetime_points']} acumulados',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
                const SizedBox(height: 12),
                if (((row['points_balance'] as num?)?.toInt() ?? 0) >= 100)
                  AppButton(
                    label: _isConverting ? 'Convirtiendo...' : 'Convertir a \$${(((row['points_balance'] as num).toInt() ~/ 100)).toStringAsFixed(2)} BOB en Billetera',
                    icon: const Icon(Icons.currency_exchange),
                    isLoading: _isConverting,
                    expand: true,
                    onPressed: _isConverting ? null : () => _convertPoints(row),
                  )
                else
                  const Text('Mínimo 100 puntos para convertir a saldo', style: TextStyle(fontSize: 11, color: Colors.grey)),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],
        if (_loyaltyMovements != null && _loyaltyMovements!.isNotEmpty) ...[
          const SizedBox(height: 8),
          Center(
            child: AppButton(
              label: 'Ver historial de puntos (${_loyaltyMovements!.length})',
              variant: AppButtonVariant.outlined,
              icon: const Icon(Icons.history, size: 18),
              onPressed: _showPointsHistoryModal,
            ),
          ),
          const SizedBox(height: 12),
        ],
      ],
    );
  }
}
