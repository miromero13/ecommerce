import 'dart:async';

import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';

import '../../core/config/app_config.dart';

/// CU5 live try-on: opens the web's live camera fitting room (MediaPipe) inside a WebView.
class VirtualTryOnPage extends StatefulWidget {
  const VirtualTryOnPage({
    super.key,
    required this.productId,
    required this.variantId,
    required this.accessToken,
  });

  final String productId;
  final String? variantId;
  final String accessToken;

  @override
  State<VirtualTryOnPage> createState() => _VirtualTryOnPageState();
}

class _VirtualTryOnPageState extends State<VirtualTryOnPage> {
  WebViewController? _controller;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    unawaited(_initializeWebView());
  }

  Future<void> _initializeWebView() async {
    final base = AppConfig.frontendUrl.trim().replaceFirst(RegExp(r'/$'), '');
    final uri = Uri.tryParse(base)?.replace(
      path: '/mobile-try-on',
      queryParameters: {
        'product': widget.productId,
        if (widget.variantId != null) 'variant': widget.variantId!,
      },
      // The fragment never leaves the device: the page reads the token from it.
      fragment: 'token=${widget.accessToken}',
    );
    if (uri == null || (uri.scheme != 'http' && uri.scheme != 'https')) {
      setState(() => _errorMessage = 'La dirección del probador web no es válida.');
      return;
    }

    final cameraStatus = await Permission.camera.request();
    if (!mounted) return;
    if (!cameraStatus.isGranted) {
      setState(() {
        _isLoading = false;
        _errorMessage = cameraStatus.isPermanentlyDenied
            ? 'El acceso a la cámara está desactivado. Actívalo en Ajustes para usar el vestidor.'
            : 'Se necesita la cámara para usar el vestidor en vivo.';
      });
      return;
    }

    final controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageFinished: (_) {
            if (mounted) setState(() => _isLoading = false);
          },
          onWebResourceError: (error) {
            if (!mounted || error.isForMainFrame == false) return;
            setState(() {
              _isLoading = false;
              _errorMessage = 'No se pudo cargar el vestidor en vivo.';
            });
          },
        ),
      );

    if (controller.platform is AndroidWebViewController) {
      final android = controller.platform as AndroidWebViewController;
      // getUserMedia inside the page asks for the camera: grant only that.
      unawaited(
        android.setOnPlatformPermissionRequest((request) {
          if (request.types.every((t) => t == WebViewPermissionResourceType.camera)) {
            unawaited(request.grant());
          } else {
            unawaited(request.deny());
          }
        }),
      );
      unawaited(android.setMediaPlaybackRequiresUserGesture(false));
    }

    if (!mounted) return;
    setState(() => _controller = controller);
    unawaited(controller.loadRequest(uri));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Vestidor 3D (Cámara en vivo)'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          tooltip: 'Cerrar',
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: _errorMessage != null
          ? _ErrorView(message: _errorMessage!)
          : _controller == null
          ? const Center(child: CircularProgressIndicator())
          : Stack(
              children: [
                WebViewWidget(controller: _controller!),
                if (_isLoading)
                  const ColoredBox(
                    color: Colors.white,
                    child: Center(child: CircularProgressIndicator()),
                  ),
              ],
            ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48),
            const SizedBox(height: 16),
            Text(message, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
