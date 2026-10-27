import 'dart:convert';

import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/network/api_response.dart';
import 'app_snack_bar.dart';

/// Simulated QR payment (platform collection account). Returns true once paid.
class QrPaymentDialog extends StatefulWidget {
  const QrPaymentDialog({super.key, required this.client, required this.qr, required this.title});

  final ApiClient client;
  final Map<String, dynamic> qr;
  final String title;

  static Future<bool> show(BuildContext context, ApiClient client, Map<String, dynamic> qr,
      {String title = 'Escanea el código QR con tu app bancaria'}) async {
    final paid = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (_) => QrPaymentDialog(client: client, qr: qr, title: title),
    );
    return paid ?? false;
  }

  @override
  State<QrPaymentDialog> createState() => _QrPaymentDialogState();
}

class _QrPaymentDialogState extends State<QrPaymentDialog> {
  late Map<String, dynamic> _qr = widget.qr;
  bool _busy = false;

  String get _reference => _qr['reference'].toString();

  Future<void> _call(Future<ApiResponse<dynamic>> Function() action, {bool quietWhenPending = false}) async {
    setState(() => _busy = true);
    try {
      final response = await action();
      final data = response.data;
      if (data is Map) _qr = Map<String, dynamic>.from(data);
      if (!mounted) return;
      final status = _qr['status'];
      if (status == 'paid' || status == 'used') {
        AppSnackBar.show(context, response.message, tone: AppSnackBarTone.success);
        Navigator.of(context).pop(true);
        return;
      }
      if (!quietWhenPending) {
        AppSnackBar.show(context, 'Aún no recibimos el pago.', tone: AppSnackBarTone.neutral);
      }
    } catch (error) {
      if (mounted) {
        AppSnackBar.show(context, error is ApiException ? error.message : 'No se pudo verificar el pago.',
            tone: AppSnackBarTone.error);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final image = base64Decode(_qr['qr_image'].toString().split(',').last);
    return AlertDialog(
      title: Text(widget.title, style: Theme.of(context).textTheme.titleMedium),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Image.memory(image, width: 200, height: 200, gaplessPlayback: true),
          const SizedBox(height: 8),
          Text('${_qr['amount']} ${_qr['currency'].toString().toUpperCase()}',
              style: Theme.of(context).textTheme.titleLarge),
          Text('Referencia $_reference', style: Theme.of(context).textTheme.bodySmall),
          if (_qr['status'] == 'expired')
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text('El código QR expiró. Genera uno nuevo.'),
            ),
          const SizedBox(height: 8),
          Text('En producción el banco confirma el pago automáticamente.',
              textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
      actions: [
        TextButton(onPressed: _busy ? null : () => Navigator.of(context).pop(false), child: const Text('Cerrar')),
        TextButton(
          onPressed: _busy ? null : () => _call(() => widget.client.get<dynamic>('payments/qr/$_reference')),
          child: const Text('Verificar pago'),
        ),
        FilledButton(
          onPressed: _busy || _qr['status'] != 'pending'
              ? null
              : () => _call(() => widget.client.post<dynamic>('payments/qr/$_reference/simulate-payment')),
          child: const Text('Simular pago (demo)'),
        ),
      ],
    );
  }
}
