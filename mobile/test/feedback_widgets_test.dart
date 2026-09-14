import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/theme.dart';
import 'package:mobile/shared/widgets/app_bottom_sheet.dart';
import 'package:mobile/shared/widgets/app_button.dart';
import 'package:mobile/shared/widgets/app_dialog.dart';
import 'package:mobile/shared/widgets/app_empty_view.dart';
import 'package:mobile/shared/widgets/app_error_view.dart';
import 'package:mobile/shared/widgets/app_snack_bar.dart';

void main() {
  testWidgets('abre y cierra un diálogo', (tester) async {
    await tester.pumpWidget(
      _host(
        Builder(
          builder: (context) => AppButton(
            label: 'Abrir',
            onPressed: () => AppDialog.show<void>(
              context: context,
              title: 'Título',
              content: const Text('Contenido'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cerrar'),
                ),
              ],
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Abrir'));
    await tester.pumpAndSettle();
    expect(find.text('Contenido'), findsOneWidget);

    await tester.tap(find.text('Cerrar'));
    await tester.pumpAndSettle();
    expect(find.text('Contenido'), findsNothing);
  });

  testWidgets('abre y cierra una hoja inferior', (tester) async {
    await tester.pumpWidget(
      _host(
        Builder(
          builder: (context) => AppButton(
            label: 'Abrir',
            onPressed: () => AppBottomSheet.show<void>(
              context: context,
              title: 'Filtros',
              child: AppButton(
                label: 'Cerrar',
                onPressed: () => Navigator.pop(context),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Abrir'));
    await tester.pumpAndSettle();
    expect(find.text('Filtros'), findsOneWidget);

    await tester.tap(find.text('Cerrar'));
    await tester.pumpAndSettle();
    expect(find.text('Filtros'), findsNothing);
  });

  testWidgets('ejecuta acciones de error y vacío', (tester) async {
    var retries = 0;
    var actions = 0;

    await tester.pumpWidget(
      _host(
        Column(
          children: [
            AppErrorView(message: 'Error', onRetry: () => retries++),
            AppEmptyView(
              message: 'Vacío',
              actionLabel: 'Acción',
              onAction: () => actions++,
            ),
          ],
        ),
      ),
    );

    await tester.tap(find.text('Reintentar'));
    await tester.tap(find.text('Acción'));
    expect(retries, 1);
    expect(actions, 1);
  });

  testWidgets('muestra un snackbar con el mensaje recibido', (tester) async {
    await tester.pumpWidget(
      _host(
        Builder(
          builder: (context) => AppButton(
            label: 'Mostrar',
            onPressed: () => AppSnackBar.show(context, 'Guardado'),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Mostrar'));
    await tester.pump();
    expect(find.text('Guardado'), findsOneWidget);
  });
}

Widget _host(Widget child) {
  return MaterialApp(
    theme: buildAppTheme(),
    home: Scaffold(body: child),
  );
}
