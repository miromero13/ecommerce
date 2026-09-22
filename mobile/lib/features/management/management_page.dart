import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../shared/widgets/app_card.dart';
import '../../shared/widgets/app_section_title.dart';
import '../notifications/notification_controller.dart';

class ManagementPage extends StatelessWidget {
  const ManagementPage({super.key, this.notificationController});

  final NotificationController? notificationController;

  @override
  Widget build(BuildContext context) {
    if (notificationController == null) return _buildList(context);
    return ListenableBuilder(
      listenable: notificationController!,
      builder: (context, _) => _buildList(context),
    );
  }

  Widget _buildList(BuildContext context) {
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
        const SizedBox(height: 12),
        _ManagementCard(
          icon: Icons.notifications_none,
          title: 'Notificaciones',
          subtitle: 'Consulta novedades y cambios de estado.',
          badge: notificationController?.unreadCount,
          onTap: () => Navigator.of(context).pushNamed(AppRoutes.notifications),
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
    this.badge,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final int? badge;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      onTap: onTap,
      child: Row(
        children: [
          CircleAvatar(child: Icon(icon)),
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
          if (badge != null && badge! > 0) Badge(label: Text('$badge')),
          const SizedBox(width: 8),
          const Icon(Icons.chevron_right),
        ],
      ),
    );
  }
}
