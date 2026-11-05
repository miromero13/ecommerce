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
          icon: Icons.local_shipping_outlined,
          title: 'Mis envíos',
          subtitle: 'Seguimiento de pedidos a domicilio y código PIN de entrega.',
          onTap: () => Navigator.of(context).pushNamed(AppRoutes.deliveries),
        ),
        const SizedBox(height: 12),
        _ManagementCard(
          icon: Icons.assignment_return_outlined,
          title: 'Mis devoluciones y cambios',
          subtitle: 'Gestiona solicitudes de RMA, cambios de talle y fichas.',
          onTap: () => Navigator.of(context).pushNamed(AppRoutes.returns),
        ),
        const SizedBox(height: 12),
        _ManagementCard(
          icon: Icons.favorite_border,
          title: 'Lista de deseos',
          subtitle: 'Tus prendas favoritas, listas para mover al carrito.',
          onTap: () => Navigator.of(context).pushNamed(AppRoutes.wishlist),
        ),
        const SizedBox(height: 12),
        _ManagementCard(
          icon: Icons.account_balance_wallet_outlined,
          title: 'Mi Billetera Digital',
          subtitle: 'Saldo en Bs, conversión de puntos de fidelidad y Gift Cards.',
          onTap: () => Navigator.of(context).pushNamed(AppRoutes.wallet),
        ),
        const SizedBox(height: 12),
        _ManagementCard(
          icon: Icons.sync_problem_outlined,
          title: 'Cola de operaciones offline',
          subtitle: 'Ventas y reservas retenidas localmente pendientes de sincronizar.',
          onTap: () => Navigator.of(context).pushNamed(AppRoutes.offlineQueue),
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
