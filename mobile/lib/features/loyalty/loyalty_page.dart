import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../../shared/widgets/app_snack_bar.dart';
import '../auth/auth_controller.dart';

/// CU17: points and tier per company (1 point per 10 Bs paid, 10 points = 1 Bs) and the movement history.
class LoyaltyPage extends StatefulWidget {
  const LoyaltyPage({super.key, required this.authController});

  final AuthController authController;

  @override
  State<LoyaltyPage> createState() => _LoyaltyPageState();
}

class _LoyaltyPageState extends State<LoyaltyPage> {
  late final ApiClient _client = ApiClient(
    tokenProvider: () => widget.authController.accessToken,
    onUnauthorized: widget.authController.handleUnauthorized,
  );
  List<Map<String, dynamic>>? _balances;
  List<Map<String, dynamic>> _movements = const [];

  static const _labels = {'earn': 'Ganados', 'redeem': 'Canjeados', 'refund': 'Devueltos'};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<List<Map<String, dynamic>>> _rows(String path) async {
    final response = await _client.get<List<dynamic>>(path, parser: (value) => value as List);
    return (response.data ?? const []).map((row) => Map<String, dynamic>.from(row as Map)).toList();
  }

  Future<void> _load() async {
    try {
      final results = await Future.wait([_rows('loyalty/balance'), _rows('loyalty/transactions')]);
      if (mounted) {
        setState(() {
          _balances = results[0];
          _movements = results[1];
        });
      }
    } catch (error) {
      if (!mounted) return;
      setState(() => _balances = const []);
      AppSnackBar.show(context, error is ApiException ? error.message : 'No se pudieron cargar tus puntos.',
          tone: AppSnackBarTone.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final balances = _balances;
    if (balances == null) return const AppLoading();
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const AppSectionTitle(
            title: 'Mis puntos',
            subtitle: '1 punto por cada 10 Bs pagados · 10 puntos = 1 Bs. Bronce < 500, Plata 500-1499, Oro ≥ 1500.',
          ),
          const SizedBox(height: 16),
          if (balances.isEmpty)
            const AppEmptyView(title: 'Aún no tienes puntos', message: 'Ganarás puntos con tu primera compra pagada.'),
          for (final row in balances) ...[
            AppCard(
              child: ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(row['tenant_name'].toString()),
                subtitle: Text('${row['lifetime_points']} acumulados · equivalen a ${row['balance_value']} Bs'),
                trailing: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('${row['points_balance']} pts', style: Theme.of(context).textTheme.titleMedium),
                    Text(row['tier'].toString()),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],
          if (_movements.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text('Movimientos', style: Theme.of(context).textTheme.titleMedium),
            for (final row in _movements)
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text('${_labels[row['type']] ?? row['type']} · ${row['tenant_name']}'),
                subtitle: Text(row['source_type'] == 'order' ? 'Pedido web' : 'Compra en tienda'),
                trailing: Text('${row['type'] == 'redeem' ? '-' : '+'}${row['points']}'),
              ),
          ],
        ],
      ),
    );
  }
}
