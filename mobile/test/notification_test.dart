import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/notifications/notification_api.dart';
import 'package:mobile/features/notifications/notification_controller.dart';
import 'package:mobile/features/notifications/notification_models.dart';

void main() {
  test('parses a notification and preserves navigation data', () {
    final item = NotificationItem.fromJson(_json('notification-1'));

    expect(item.id, 'notification-1');
    expect(item.isRead, isFalse);
    expect(item.data['destination'], 'orders');
    expect(item.data['order_id'], 'order-1');
  });

  test('loads, marks a notification, and updates the badge', () async {
    final controller = NotificationController(api: _FakeNotificationApi());

    await controller.load();
    expect(controller.notifications, hasLength(1));
    expect(controller.unreadCount, 1);

    await controller.markRead('notification-1');

    expect(controller.notifications.single.isRead, isTrue);
    expect(controller.unreadCount, 0);
  });

  test('marks all notifications as read', () async {
    final controller = NotificationController(api: _FakeNotificationApi());

    await controller.load();
    await controller.markAllRead();

    expect(controller.unreadCount, 0);
    expect(controller.notifications.single.isRead, isTrue);
  });
}

class _FakeNotificationApi extends NotificationApi {
  _FakeNotificationApi() : super();

  @override
  Future<NotificationListResult> list() async {
    return NotificationListResult(
      notifications: [NotificationItem.fromJson(_json('notification-1'))],
      message: 'Notificaciones obtenidas exitosamente',
    );
  }

  @override
  Future<int> unreadCount() async => 1;

  @override
  Future<NotificationItem> markRead(String id) async {
    return NotificationItem(
      id: id,
      title: 'Pedido creado',
      body: 'Tu pedido fue creado.',
      data: const {'destination': 'orders', 'order_id': 'order-1'},
      createdAt: DateTime.utc(2026, 9, 1),
      readAt: DateTime.utc(2026, 9, 2),
    );
  }

  @override
  Future<void> markAllRead() async {}
}

Map<String, dynamic> _json(String id) {
  return {
    'id': id,
    'title': 'Pedido creado',
    'body': 'Tu pedido fue creado.',
    'data': {'destination': 'orders', 'order_id': 'order-1'},
    'read_at': null,
    'created_at': '2026-09-01T00:00:00Z',
  };
}
