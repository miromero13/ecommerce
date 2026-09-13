import 'package:flutter/material.dart';

class ProductImage extends StatelessWidget {
  const ProductImage({
    super.key,
    this.imageUrl,
    this.imageUrls = const [],
    this.fit = BoxFit.cover,
    this.borderRadius = const BorderRadius.all(Radius.circular(10)),
  });

  final String? imageUrl;
  final List<String> imageUrls;
  final BoxFit fit;
  final BorderRadius borderRadius;

  List<String> get _urls {
    final primary = imageUrl?.trim();
    return [
      if (primary != null && primary.isNotEmpty) primary,
      ...imageUrls.map((url) => url.trim()).where((url) => url.isNotEmpty),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final urls = _urls;
    final content = switch (urls.length) {
      0 => _placeholder(context),
      1 => _networkImage(context, urls.first),
      _ => Stack(
        fit: StackFit.expand,
        children: [
          PageView.builder(
            itemCount: urls.length,
            itemBuilder: (_, index) => _networkImage(context, urls[index]),
          ),
          Positioned(
            bottom: 10,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                for (var index = 0; index < urls.length; index++)
                  Container(
                    width: 6,
                    height: 6,
                    margin: const EdgeInsets.symmetric(horizontal: 2),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.85),
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    };

    return ClipRRect(borderRadius: borderRadius, child: content);
  }

  Widget _networkImage(BuildContext context, String url) {
    return Image.network(
      url,
      fit: fit,
      width: double.infinity,
      height: double.infinity,
      errorBuilder: (_, _, _) => _placeholder(context),
      loadingBuilder: (_, child, progress) =>
          progress == null ? child : _placeholder(context, loading: true),
    );
  }

  Widget _placeholder(BuildContext context, {bool loading = false}) {
    final colorScheme = Theme.of(context).colorScheme;
    return ColoredBox(
      color: colorScheme.surfaceContainerHighest,
      child: Center(
        child: loading
            ? SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: colorScheme.primary,
                ),
              )
            : Icon(
                Icons.image_outlined,
                color: colorScheme.onSurfaceVariant,
                size: 32,
              ),
      ),
    );
  }
}
