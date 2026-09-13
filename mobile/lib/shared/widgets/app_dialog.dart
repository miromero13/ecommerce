import 'package:flutter/material.dart';

abstract final class AppDialog {
  static Future<T?> show<T>({
    required BuildContext context,
    required String title,
    required Widget content,
    List<Widget>? actions,
    bool barrierDismissible = true,
  }) {
    return showDialog<T>(
      context: context,
      barrierDismissible: barrierDismissible,
      builder: (context) =>
          AlertDialog(title: Text(title), content: content, actions: actions),
    );
  }
}
