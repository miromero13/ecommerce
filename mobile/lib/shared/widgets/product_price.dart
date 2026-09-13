import 'package:flutter/material.dart';

class ProductPrice extends StatelessWidget {
  const ProductPrice({
    super.key,
    required this.price,
    this.currency = 'Bs',
    this.style,
  });

  final num price;
  final String currency;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    return Text(
      '$currency ${price.toStringAsFixed(2)}',
      style:
          style ??
          Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
    );
  }
}
