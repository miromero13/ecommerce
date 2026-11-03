import 'dart:convert';
import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../shared/widgets/app_badge.dart';
import '../../shared/widgets/app_button.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_dialog.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../../shared/widgets/app_text_field.dart';
import '../auth/auth_controller.dart';

/// CU18: Emitir y comprar tarjetas de regalo (Gift Cards) en móvil.
class GiftCardsPage extends StatefulWidget {
  const GiftCardsPage({super.key, required this.authController});

  final AuthController authController;

  @override
  State<GiftCardsPage> createState() => _GiftCardsPageState();
}

class _GiftCardsPageState extends State<GiftCardsPage> {
  late final ApiClient _client = ApiClient(
    tokenProvider: () => widget.authController.accessToken,
    onUnauthorized: widget.authController.handleUnauthorized,
  );

  final _recipientNameController = TextEditingController();
  final _recipientEmailController = TextEditingController();
  final _customMessageController = TextEditingController();
  final _customAmountController = TextEditingController();

  final List<int> _presets = [20, 50, 100];
  int _selectedAmount = 50;
  bool _isCustomAmount = false;
  bool _isSubmitting = false;

  List<Map<String, dynamic>>? _myCards;

  @override
  void initState() {
    super.initState();
    _loadPurchases();
  }

  @override
  void dispose() {
    _recipientNameController.dispose();
    _recipientEmailController.dispose();
    _customMessageController.dispose();
    _customAmountController.dispose();
    super.dispose();
  }

  Future<void> _loadPurchases() async {
    try {
      final res = await _client.get<List<dynamic>>(
        'gift-cards/my-purchases',
        parser: (data) => data as List,
      );
      if (mounted) {
        setState(() {
          _myCards = (res.data ?? const [])
              .map((row) => Map<String, dynamic>.from(row as Map))
              .toList();
        });
      }
    } catch (_) {
      if (mounted) setState(() => _myCards = const []);
    }
  }

  Future<void> _purchase() async {
    final amount = _isCustomAmount
        ? (double.tryParse(_customAmountController.text.trim()) ?? 0.0)
        : _selectedAmount.toDouble();
    final name = _recipientNameController.text.trim();
    final email = _recipientEmailController.text.trim();
    final msg = _customMessageController.text.trim();

    if (amount < 10) {
      AppSnackBar.show(context, 'El importe debe ser mayor o igual a $10.00',
          tone: AppSnackBarTone.error);
      return;
    }
    if (name.isEmpty) {
      AppSnackBar.show(context, 'Ingresa el nombre del destinatario',
          tone: AppSnackBarTone.error);
      return;
    }
    if (!email.contains('@')) {
      AppSnackBar.show(context, 'Ingresa un correo electrónico válido',
          tone: AppSnackBarTone.error);
      return;
    }

    setState(() => _isSubmitting = true);
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
      AppSnackBar.show(
        context,
        res.message ?? 'Tarjeta de regalo adquirida y enviada por correo al destinatario',
        tone: AppSnackBarTone.success,
      );

      _recipientNameController.clear();
      _recipientEmailController.clear();
      _customMessageController.clear();
      _customAmountController.clear();
      setState(() => _isCustomAmount = false);
      _loadPurchases();
    } catch (error) {
      if (!mounted) return;
      AppSnackBar.show(
        context,
        error is ApiException ? error.message : 'Error al procesar la compra',
        tone: AppSnackBarTone.error,
      );
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  void _showQrDialog(Map<String, dynamic> card) {
    final qrData = card['qr_code_url']?.toString();
    AppDialog.show<void>(
      context: context,
      title: card['code']?.toString() ?? 'Gift Card',
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (qrData != null && qrData.startsWith('data:image')) ...[
            Image.memory(
              base64Decode(qrData.split(',').last),
              width: 200,
              height: 200,
              fit: BoxFit.contain,
            ),
            const SizedBox(height: 12),
          ],
          Text(
            'Valor: \$${card['amount']} BOB',
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(height: 4),
          Text('Para: ${card['recipient_name']}'),
          Text('Estado: ${card['status']}'),
        ],
      ),
      actions: [
        AppButton(
          label: 'Cerrar',
          variant: AppButtonVariant.text,
          onPressed: () => Navigator.of(context).pop(),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final myCards = _myCards;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const AppSectionTitle(
          title: 'Tarjetas de Regalo',
          subtitle: 'Comprá un voucher prepagado con dedicatoria personalizada y código QR.',
        ),
        const SizedBox(height: 16),

        // Tarjeta de Compra
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Seleccioná el monto', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              Row(
                children: [
                  for (final p in _presets)
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 4),
                        child: AppButton(
                          label: '\$$p BOB',
                          variant: (!_isCustomAmount && _selectedAmount == p)
                              ? AppButtonVariant.primary
                              : AppButtonVariant.outlined,
                          onPressed: () => setState(() {
                            _isCustomAmount = false;
                            _selectedAmount = p;
                          }),
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () {
                  setState(() => _isCustomAmount = !_isCustomAmount);
                },
                child: Text(_isCustomAmount ? 'Usar monto predefinido' : '+ Monto personalizado'),
              ),
              if (_isCustomAmount) ...[
                const SizedBox(height: 8),
                AppTextField(
                  controller: _customAmountController,
                  label: 'Monto en BOB (mínimo 10.00)',
                  keyboardType: TextInputType.number,
                ),
              ],
              const SizedBox(height: 16),
              AppTextField(
                controller: _recipientNameController,
                label: 'Nombre del destinatario',
              ),
              const SizedBox(height: 12),
              AppTextField(
                controller: _recipientEmailController,
                label: 'Correo electrónico',
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 12),
              AppTextField(
                controller: _customMessageController,
                label: 'Mensaje personal o dedicatoria (opcional)',
                maxLines: 2,
              ),
              const SizedBox(height: 16),
              AppButton(
                label: _isSubmitting ? 'Procesando...' : 'Comprar Tarjeta de Regalo',
                icon: const Icon(Icons.card_giftcard),
                isLoading: _isSubmitting,
                onPressed: _isSubmitting ? null : _purchase,
              ),
            ],
          ),
        ),

        const SizedBox(height: 24),
        Text('Mis Gift Cards Compradas', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),

        if (myCards == null)
          const AppLoading()
        else if (myCards.isEmpty)
          const AppEmptyView(
            title: 'Sin Gift Cards aún',
            message: 'Tus compras de tarjetas de regalo aparecerán aquí.',
          )
        else
          for (final card in myCards) ...[
            AppCard(
              child: ListTile(
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(
                  backgroundColor: card['status'] == 'active' ? Colors.green.shade100 : Colors.grey.shade200,
                  child: Icon(
                    Icons.card_giftcard,
                    color: card['status'] == 'active' ? Colors.green.shade800 : Colors.grey.shade600,
                  ),
                ),
                title: Text(card['code']?.toString() ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text('Para: ${card['recipient_name']} · \$${card['amount']} BOB\nEstado: ${card['status']}'),
                isThreeLine: true,
                trailing: IconButton(
                  icon: const Icon(Icons.qr_code),
                  tooltip: 'Ver QR',
                  onPressed: () => _showQrDialog(card),
                ),
              ),
            ),
            const SizedBox(height: 8),
          ],
      ],
    );
  }
}
