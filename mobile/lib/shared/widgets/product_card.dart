import 'package:flutter/material.dart';

import 'app_badge.dart';
import 'app_card.dart';
import 'product_image.dart';
import 'product_price.dart';

class ProductCard extends StatelessWidget {
  const ProductCard({
    super.key,
    required this.name,
    required this.price,
    this.originalPrice,
    this.imageUrl,
    this.variantImageUrls = const [],
    this.badge,
    this.tenantName,
    this.onTap,
    this.onAddToCart,
    this.onReserve,
    this.isAddingToCart = false,
    this.imageAspectRatio = 1.2,
  });

  final String name;
  final num price;
  final num? originalPrice;
  final String? imageUrl;
  final List<String> variantImageUrls;
  final String? badge;
  final String? tenantName;
  final VoidCallback? onTap;
  final VoidCallback? onAddToCart;
  final VoidCallback? onReserve;
  final bool isAddingToCart;
  final double imageAspectRatio;

  @override
  Widget build(BuildContext context) {
    final hasDiscount = originalPrice != null && originalPrice! > price;

    return AppCard(
      onTap: onTap,
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Stack(
            children: [
              AspectRatio(
                aspectRatio: imageAspectRatio,
                child: ProductImage(
                  imageUrl: imageUrl,
                  imageUrls: variantImageUrls,
                  borderRadius: const BorderRadius.vertical(
                    top: Radius.circular(10),
                  ),
                ),
              ),
              if (badge != null || hasDiscount)
                Positioned(
                  top: 8,
                  left: 8,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (hasDiscount) ...[
                        const AppBadge(
                          label: 'OFERTA',
                          tone: AppBadgeTone.accent,
                        ),
                        const SizedBox(width: 4),
                      ],
                      if (badge != null)
                        AppBadge(label: badge!, tone: AppBadgeTone.neutral),
                    ],
                  ),
                ),
              Positioned(
                top: 6,
                right: 6,
                child: Material(
                  color: Colors.white.withValues(alpha: 0.9),
                  shape: const CircleBorder(),
                  elevation: 2,
                  child: InkWell(
                    customBorder: const CircleBorder(),
                    onTap: onTap,
                    child: const Padding(
                      padding: EdgeInsets.all(5),
                      child: Icon(
                        Icons.visibility_outlined,
                        size: 16,
                        color: Colors.black87,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                if (tenantName != null && tenantName!.isNotEmpty) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 6,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      '🏪 $tenantName',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 9.5,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey.shade700,
                      ),
                    ),
                  ),
                  const SizedBox(height: 3),
                ],
                Text(
                  name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(
                    context,
                  ).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 3),
                ProductPrice(price: price, originalPrice: originalPrice),
                if (onAddToCart != null || onReserve != null) ...[
                  const SizedBox(height: 6),
                  if (onAddToCart != null)
                    SizedBox(
                      width: double.infinity,
                      height: 28,
                      child: FilledButton.icon(
                        style: FilledButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 6),
                          textStyle: const TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        onPressed: isAddingToCart ? null : onAddToCart,
                        icon: isAddingToCart
                            ? const SizedBox(
                                width: 10,
                                height: 10,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(
                                Icons.shopping_cart_outlined,
                                size: 13,
                              ),
                        label: Text(
                          isAddingToCart ? 'Agregando...' : 'Al carrito',
                        ),
                      ),
                    ),
                  if (onReserve != null) ...[
                    const SizedBox(height: 4),
                    SizedBox(
                      width: double.infinity,
                      height: 28,
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 6),
                          textStyle: const TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        onPressed: onReserve,
                        icon: const Icon(
                          Icons.bookmark_border_outlined,
                          size: 13,
                        ),
                        label: const Text('Reservar'),
                      ),
                    ),
                  ],
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
