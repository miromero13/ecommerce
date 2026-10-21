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

  @override
  Widget build(BuildContext context) {
    final hasDiscount = originalPrice != null && originalPrice! > price;

    return AppCard(
      onTap: onTap,
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Stack(
            children: [
              AspectRatio(
                aspectRatio: 1,
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
                  top: 10,
                  left: 10,
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
                top: 8,
                right: 8,
                child: Material(
                  color: Colors.white.withValues(alpha: 0.9),
                  shape: const CircleBorder(),
                  elevation: 2,
                  child: InkWell(
                    customBorder: const CircleBorder(),
                    onTap: onTap,
                    child: const Padding(
                      padding: EdgeInsets.all(6),
                      child: Icon(
                        Icons.visibility_outlined,
                        size: 18,
                        color: Colors.black87,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
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
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey.shade700,
                      ),
                    ),
                  ),
                  const SizedBox(height: 4),
                ],
                Text(
                  name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(
                    context,
                  ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 4),
                ProductPrice(price: price, originalPrice: originalPrice),
                if (onAddToCart != null || onReserve != null) ...[
                  const SizedBox(height: 8),
                  if (onAddToCart != null)
                    SizedBox(
                      width: double.infinity,
                      height: 32,
                      child: FilledButton.icon(
                        style: FilledButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          textStyle: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        onPressed: isAddingToCart ? null : onAddToCart,
                        icon: isAddingToCart
                            ? const SizedBox(
                                width: 12,
                                height: 12,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(
                                Icons.shopping_cart_outlined,
                                size: 14,
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
                      height: 30,
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          textStyle: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        onPressed: onReserve,
                        icon: const Icon(
                          Icons.bookmark_border_outlined,
                          size: 14,
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
