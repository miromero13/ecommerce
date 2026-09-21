import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../shared/widgets/app_empty_view.dart';
import '../../shared/widgets/app_error_view.dart';
import '../../shared/widgets/app_loading.dart';
import '../../shared/widgets/app_section_title.dart';
import '../auth/auth_controller.dart';
import '../auth/login_dialog.dart';
import 'notification_controller.dart';
import 'notification_models.dart';

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({
    super.key,
    required this.authController,
    this.controller,
  });

  final AuthController authController;
  final NotificationController? controller;

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  late final NotificationController _controller;
  late final bool _ownsController;

  @override
  void initState() {
    super.initState();
    _ownsController = widget.controller == null;
    _controller =
        widget.controller ??
        NotificationController(authController: widget.authController);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (widget.authController.isAuthenticated) _controller.load();
    });
  }

  @override
  void dispose() {
    if (_ownsController) _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.authController.isAuthenticated) {
      return AppEmptyView(
        title: 'Notificaciones privadas',
        message: 'Inicia sesión para consultar tus notificaciones.',
        actionLabel: 'Iniciar sesión',
        onAction: () => LoginDialog.show(
          context: context,
          controller: widget.authController,
        ),
      );
    }
    return ListenableBuilder(
      listenable: _controller,
      builder: (context, _) => _buildContent(context),
    );
  }

  Widget _buildContent(BuildContext context) {
    if (_controller.status == NotificationControllerStatus.error &&
        _controller.notifications.isEmpty) {
      return AppErrorView(
        message:
            _controller.errorMessage ??
            'No se pudieron cargar las notificaciones.',
        onRetry: _controller.load,
      );
    }
    if (_controller.status == NotificationControllerStatus.loading &&
        _controller.notifications.isEmpty) {
      return const AppLoading(message: 'Cargando notificaciones...');
    }
    return RefreshIndicator(
      onRefresh: _controller.load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          if (_controller.status == NotificationControllerStatus.loading)
            const LinearProgressIndicator(minHeight: 2),
          AppSectionTitle(
            title: 'Notificaciones',
            subtitle: _controller.unreadCount == 0
                ? 'Estás al día.'
                : '${_controller.unreadCount} sin leer',
            action: _controller.unreadCount == 0
                ? null
                : TextButton(
                    onPressed: _controller.markAllRead,
                    child: const Text('Leer todas'),
                  ),
          ),
          const SizedBox(height: 12),
          if (_controller.notifications.isEmpty)
            const AppEmptyView(
              title: 'Sin notificaciones',
              message: 'Aquí aparecerán tus novedades.',
            )
          else
            for (final item in _controller.notifications) ...[
              _NotificationTile(item: item, onTap: () => _open(item)),
              const SizedBox(height: 8),
            ],
        ],
      ),
    );
  }

  Future<void> _open(NotificationItem item) async {
    await _controller.markRead(item.id);
    if (!mounted) return;
    openNotificationDestination(context, item.data);
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({required this.item, required this.onTap});

  final NotificationItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: item.isRead
          ? null
          : Theme.of(context).colorScheme.primaryContainer,
      child: ListTile(
        onTap: onTap,
        leading: Icon(
          item.isRead ? Icons.notifications_none : Icons.notifications_active,
        ),
        title: Text(
          item.title,
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        subtitle: Text(item.body),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }
}

void openNotificationDestination(
  BuildContext context,
  Map<String, dynamic> data,
) {
  final destination = data['destination']?.toString();
  final idKey = destination == 'orders'
      ? 'order_id'
      : destination == 'reservations'
      ? 'reservation_id'
      : null;
  final id = idKey == null ? null : data[idKey]?.toString();
  if (destination == 'orders' && id != null && id.isNotEmpty) {
    Navigator.of(context).pushNamed(AppRoutes.orders, arguments: id);
  } else if (destination == 'reservations' && id != null && id.isNotEmpty) {
    Navigator.of(context).pushNamed(AppRoutes.reservations, arguments: id);
  } else {
    Navigator.of(context).pushNamed(AppRoutes.notifications);
  }
}
