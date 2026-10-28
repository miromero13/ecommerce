import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../features/auth/auth_controller.dart';
import 'app_snack_bar.dart';

/// Every payment issues a receipt (comprobante) that is emailed as PDF; this re-sends it to the customer.
class ReceiptEmailButton extends StatefulWidget {
  const ReceiptEmailButton({super.key, required this.authController, required this.kind, required this.sourceId});

  final AuthController authController;
  final String kind; // order | reservation_deposit
  final String sourceId;

  @override
  State<ReceiptEmailButton> createState() => _ReceiptEmailButtonState();
}

class _ReceiptEmailButtonState extends State<ReceiptEmailButton> {
  bool _busy = false;

  Future<void> _send() async {
    setState(() => _busy = true);
    final client = ApiClient(
      tokenProvider: () => widget.authController.accessToken,
      onUnauthorized: widget.authController.handleUnauthorized,
    );
    try {
      final response = await client.post<dynamic>('receipts/${widget.kind}/${widget.sourceId}/resend');
      if (mounted) AppSnackBar.show(context, response.message, tone: AppSnackBarTone.success);
    } catch (error) {
      if (mounted) {
        AppSnackBar.show(context, error is ApiException ? error.message : 'No se pudo enviar el comprobante.',
            tone: AppSnackBarTone.error);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: _busy ? null : _send,
      icon: const Icon(Icons.receipt_long_outlined),
      label: const Text('Enviar comprobante a mi correo'),
    );
  }
}
