import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';

import '../../core/config/app_config.dart';

class VirtualTryOnPage extends StatefulWidget {
  const VirtualTryOnPage({
    super.key,
    required this.productName,
    required this.garmentImageUrl,
  });

  final String productName;
  final String garmentImageUrl;

  @override
  State<VirtualTryOnPage> createState() => _VirtualTryOnPageState();
}

class _VirtualTryOnPageState extends State<VirtualTryOnPage> {
  WebViewController? _controller;
  bool _isLoading = true;
  bool _configurationSent = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    unawaited(_initializeWebView());
  }

  Future<void> _initializeWebView() async {
    final frontendUrl = AppConfig.frontendUrl.trim();
    final apiKey = AppConfig.decartApiKey.trim();
    final garmentImageUrl = widget.garmentImageUrl.trim();

    if (frontendUrl.isEmpty) {
      _errorMessage = 'The frontend URL is not configured.';
      return;
    }
    if (apiKey.isEmpty) {
      _errorMessage = 'The Decart API key is not configured.';
      return;
    }
    if (garmentImageUrl.isEmpty) {
      _errorMessage = 'This product has no image available for try-on.';
      return;
    }

    final uri = Uri.tryParse(AppConfig.decartTryOnUrl);
    if (uri == null || (uri.scheme != 'http' && uri.scheme != 'https')) {
      _errorMessage = 'The frontend URL is invalid.';
      return;
    }

    PermissionStatus cameraStatus;
    try {
      cameraStatus = await Permission.camera.request();
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _errorMessage = 'Could not request camera access for virtual try-on.';
      });
      return;
    }

    if (!mounted) return;
    if (!cameraStatus.isGranted) {
      setState(() {
        _isLoading = false;
        _errorMessage = cameraStatus.isPermanentlyDenied
            ? 'Camera access is disabled. Enable it in Settings to use virtual try-on.'
            : 'Camera access is required to use virtual try-on.';
      });
      return;
    }

    final controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) {
            if (!mounted) return;
            setState(() {
              _configurationSent = false;
              _isLoading = true;
              _errorMessage = null;
            });
          },
          onPageFinished: (_) => _sendConfiguration(),
          onWebResourceError: (_) {
            if (!mounted) return;
            setState(() {
              _isLoading = false;
              _errorMessage = 'Could not load the virtual try-on page.';
            });
          },
        ),
      );

    if (controller.platform is AndroidWebViewController) {
      final androidController = controller.platform as AndroidWebViewController;
      unawaited(
        androidController.setOnPlatformPermissionRequest((request) {
          if (request.types.length == 1 &&
              request.types.contains(WebViewPermissionResourceType.camera)) {
            unawaited(request.grant());
          } else {
            unawaited(request.deny());
          }
        }),
      );
    }

    if (!mounted) return;
    setState(() => _controller = controller);
    unawaited(controller.loadRequest(uri));
  }

  Future<void> _sendConfiguration() async {
    final controller = _controller;
    if (controller == null || _configurationSent) return;

    _configurationSent = true;
    final message = jsonEncode({
      'type': 'decart-try-on-config',
      'apiKey': AppConfig.decartApiKey.trim(),
      'garmentImageUrl': widget.garmentImageUrl.trim(),
      'productName': widget.productName,
      'keepSessionActive': true,
    });

    try {
      await controller.runJavaScript(
        'window.postMessage($message, window.location.origin);',
      );
      if (mounted) setState(() => _isLoading = false);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _errorMessage = 'Could not configure the virtual try-on page.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Probar prenda'),
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
