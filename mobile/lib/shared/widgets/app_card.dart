import 'package:flutter/material.dart';

class AppCard extends StatelessWidget {
  const AppCard({
    super.key,
    required this.child,
    this.onTap,
    this.padding = const EdgeInsets.all(16),
  });

  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final content = Padding(padding: padding, child: child);

    return Card(
      child: onTap == null
          ? content
          : InkWell(
              onTap: onTap,
              customBorder: Theme.of(context).cardTheme.shape,
              child: content,
            ),
    );
  }
}
