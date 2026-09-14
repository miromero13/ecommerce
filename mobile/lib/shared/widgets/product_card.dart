import 'package:flutter/material.dart';

import 'app_badge.dart';
import 'app_card.dart';
import 'app_icon_button.dart';
import 'product_image.dart';
import 'product_price.dart';

class ProductCard extends StatelessWidget {
  const ProductCard({
    super.key,
    required this.name,
    required this.price,
    this.imageUrl,
    this.variantImageUrls = const [],
    this.badge,
    this.onTap,
    this.onAddToCart,
  });

  final String name;
  final num price;
  final String? imageUrl;
  final List<String> variantImageUrls;
  final String? badge;
  final VoidCallback? onTap;
  final VoidCallback? onAddToCart;

  @override
  Widget build(BuildContext context) {
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
              if (badge != null)
                Positioned(
                  top: 10,
                  left: 10,
                  child: AppBadge(label: badge!, tone: AppBadgeTone.accent),
                ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 8, 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        name,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 6),
                      ProductPrice(price: price),
                    ],
                  ),
                ),
                if (onAddToCart != null)
                  AppIconButton(
                    icon: Icons.add_shopping_cart_outlined,
                    tooltip: 'Agregar al carrito',
                    onPressed: onAddToCart,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
