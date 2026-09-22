import 'package:flutter/material.dart';

class ProductPrice extends StatelessWidget {
  const ProductPrice({
    super.key,
    required this.price,
    this.originalPrice,
    this.currency = 'Bs',
    this.style,
  });

  final num price;
  final num? originalPrice;
  final String currency;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    final currentStyle =
        style ??
        Theme.of(
          context,
        ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700);
    if (originalPrice == null || originalPrice == price)
      return Text('$currency ${price.toStringAsFixed(2)}', style: currentStyle);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '$currency ${originalPrice!.toStringAsFixed(2)}',
          style: currentStyle?.copyWith(
            decoration: TextDecoration.lineThrough,
            color: Colors.grey,
          ),
        ),
        const SizedBox(width: 8),
        Text(
          '$currency ${price.toStringAsFixed(2)}',
          style: currentStyle?.copyWith(color: Colors.green),
        ),
      ],
    );
  }
}
