import 'package:flutter/material.dart';

class AppVariantOption {
  const AppVariantOption({required this.id, required this.label});

  final String id;
  final String label;
}

class AppVariantSelector extends StatelessWidget {
  const AppVariantSelector({
    super.key,
    required this.options,
    required this.selectedId,
    required this.onChanged,
  });

  final List<AppVariantOption> options;
  final String? selectedId;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final option in options)
          ChoiceChip(
            label: Text(option.label),
            selected: option.id == selectedId,
            onSelected: (_) => onChanged(option.id),
          ),
      ],
    );
  }
}
