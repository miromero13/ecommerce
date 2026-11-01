import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/config/app_config.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../shared/widgets/app_button.dart';
import '../auth/auth_controller.dart';

/// CU5 Vestidor 2D: the customer's photo goes to POST /catalog/try-on (same AI as the web).
class PhotoTryOnPage extends StatefulWidget {
  const PhotoTryOnPage({
    super.key,
    required this.authController,
    required this.variantId,
    required this.productName,
    required this.garmentImageUrl,
  });

  final AuthController authController;
  final String variantId;
  final String productName;
  final String garmentImageUrl;

  @override
  State<PhotoTryOnPage> createState() => _PhotoTryOnPageState();
}

class _PhotoTryOnPageState extends State<PhotoTryOnPage> {
  Uint8List? _photo;
  Uint8List? _result;
  bool _generating = false;
  String? _error;

  Future<void> _pick(ImageSource source) async {
    try {
      final file = await ImagePicker().pickImage(
        source: source,
        maxWidth: 1280,
        imageQuality: 85,
      );
      if (file == null) return;
      final bytes = await file.readAsBytes();
      setState(() {
        _photo = bytes;
        _result = null;
        _error = null;
      });
    } catch (_) {
      setState(() => _error = 'No se pudo acceder a la cámara o galería.');
    }
  }

  Future<void> _generate() async {
    final photo = _photo;
    if (photo == null) return;
    setState(() {
      _generating = true;
      _error = null;
    });
    try {
      final auth = widget.authController;
      final client = ApiClient(
        tokenProvider: () => auth.accessToken,
        onUnauthorized: auth.handleUnauthorized,
      );
      final response = await client.post<String>(
        'catalog/try-on',
        data: FormData.fromMap({
          'variant_id': widget.variantId,
          'photo': MultipartFile.fromBytes(photo, filename: 'photo.jpg'),
        }),
        parser: (value) => (value as Map)['image_data_url'] as String,
        // The AI model can take up to 2 minutes (backend vton_timeout_seconds).
        receiveTimeout: const Duration(seconds: 150),
      );
      final dataUrl = response.data;
      if (dataUrl == null) throw const ApiException(message: 'Respuesta inválida del servidor');
      setState(() => _result = base64Decode(dataUrl.substring(dataUrl.indexOf(',') + 1)));
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = 'No se pudo generar la prueba virtual.');
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final shown = _result ?? _photo;
    return Scaffold(
      appBar: AppBar(title: const Text('Vestidor 2D (Foto con IA)')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Row(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.network(
                  AppConfig.resolveAssetUrl(widget.garmentImageUrl) ?? widget.garmentImageUrl,
                  width: 56,
                  height: 56,
                  fit: BoxFit.cover,
                  errorBuilder: (_, _, _) => const Icon(Icons.checkroom, size: 40),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  widget.productName,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            'Tomate o elegí una foto de cuerpo entero, de frente y con buena luz. '
            'La IA te pondrá la prenda encima.',
          ),
          const SizedBox(height: 16),
          if (shown != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.memory(shown, fit: BoxFit.contain),
            ),
          if (_result != null)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text('Resultado generado por IA', textAlign: TextAlign.center),
            ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ],
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: AppButton(
                  label: 'Cámara',
                  icon: const Icon(Icons.photo_camera_outlined),
                  variant: AppButtonVariant.outlined,
                  onPressed: _generating ? null : () => _pick(ImageSource.camera),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: AppButton(
                  label: 'Galería',
                  icon: const Icon(Icons.photo_library_outlined),
                  variant: AppButtonVariant.outlined,
                  onPressed: _generating ? null : () => _pick(ImageSource.gallery),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          AppButton(
            label: _generating ? 'Generando (hasta 2 min)...' : 'Probarme la prenda',
            icon: const Icon(Icons.auto_awesome),
            isLoading: _generating,
            onPressed: _photo == null || _generating ? null : _generate,
            expand: true,
          ),
        ],
      ),
    );
  }
}
