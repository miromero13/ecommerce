import 'package:flutter/material.dart';

import 'app_icon_button.dart';

class QuantitySelector extends StatelessWidget {
  const QuantitySelector({
    super.key,
    required this.value,
    required this.onChanged,
    this.min = 1,
    this.max = 99,
  }) : assert(min <= max),
       assert(value >= min && value <= max);

  final int value;
  final ValueChanged<int> onChanged;
  final int min;
  final int max;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        AppIconButton(
          icon: Icons.remove,
          tooltip: 'Reducir cantidad',
          onPressed: value > min ? () => onChanged(value - 1) : null,
        ),
        SizedBox(
          width: 32,
          child: Text(
            '$value',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        AppIconButton(
          icon: Icons.add,
          tooltip: 'Aumentar cantidad',
          onPressed: value < max ? () => onChanged(value + 1) : null,
        ),
      ],
    );
  }
}
