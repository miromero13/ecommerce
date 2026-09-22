import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_section_title.dart';

class ManagementPage extends StatelessWidget {
  const ManagementPage({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      children: [
        const AppSectionTitle(
          title: 'Gestiones',
          subtitle: 'Consulta tus reservas y pedidos en un solo lugar.',
        ),
        const SizedBox(height: 20),
        _ManagementCard(
          icon: Icons.event_available_outlined,
          title: 'Mis reservas',
          subtitle: 'Revisa tus prendas preparadas para visitar la tienda.',
          onTap: () => Navigator.of(context).pushNamed(AppRoutes.reservations),
        ),
        const SizedBox(height: 12),
        _ManagementCard(
          icon: Icons.receipt_long_outlined,
          title: 'Mis pedidos',
          subtitle: 'Consulta compras, pagos y estados de retiro.',
          onTap: () => Navigator.of(context).pushNamed(AppRoutes.orders),
        ),
      ],
    );
  }
}

class _ManagementCard extends StatelessWidget {
  const _ManagementCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      onTap: onTap,
      child: Row(
        children: [
          CircleAvatar(
            child: Icon(icon),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(subtitle),
              ],
            ),
          ),
          const Icon(Icons.chevron_right),
        ],
      ),
    );
  }
}
