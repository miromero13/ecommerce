import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../auth/auth_controller.dart';
import 'notification_api.dart';
import 'notification_models.dart';

enum NotificationControllerStatus { idle, loading, ready, error }

class NotificationController extends ChangeNotifier {
  NotificationController({NotificationApi? api, AuthController? authController})
    : _api =
          api ??
          NotificationApi(
            client: ApiClient(
              tokenProvider: () => authController?.accessToken,
              onUnauthorized: authController?.handleUnauthorized,
            ),
          );

  final NotificationApi _api;

  NotificationControllerStatus status = NotificationControllerStatus.idle;
  List<NotificationItem> notifications = const [];
  int unreadCount = 0;
  String? errorMessage;

  Future<void> load() async {
    status = NotificationControllerStatus.loading;
    errorMessage = null;
    notifyListeners();
    try {
      final results = await Future.wait([_api.list(), _api.unreadCount()]);
      notifications = (results[0] as NotificationListResult).notifications;
      unreadCount = results[1] as int;
      status = NotificationControllerStatus.ready;
    } catch (error) {
      status = NotificationControllerStatus.error;
      errorMessage = _messageFor(error);
    }
    notifyListeners();
  }

  Future<void> refreshUnread() async {
    try {
      unreadCount = await _api.unreadCount();
      notifyListeners();
    } catch (_) {
      // Foreground delivery must not interrupt the current screen.
    }
  }

  Future<void> markRead(String id) async {
    try {
      final updated = await _api.markRead(id);
      notifications = [
        for (final item in notifications) item.id == id ? updated : item,
      ];
      if (!updated.isRead && unreadCount > 0) unreadCount--;
      if (updated.isRead) {
        unreadCount = notifications.where((item) => !item.isRead).length;
      }
      notifyListeners();
    } catch (error) {
      errorMessage = _messageFor(error);
      notifyListeners();
    }
  }

  Future<void> markAllRead() async {
    try {
      await _api.markAllRead();
      final now = DateTime.now();
      notifications = [
        for (final item in notifications)
          item.isRead
              ? item
              : NotificationItem(
                  id: item.id,
                  title: item.title,
                  body: item.body,
                  data: item.data,
                  createdAt: item.createdAt,
                  readAt: now,
                ),
      ];
      unreadCount = 0;
      notifyListeners();
    } catch (error) {
      errorMessage = _messageFor(error);
      notifyListeners();
    }
  }

  Future<void> registerToken(String token) => _api.registerToken(token);

  Future<void> unregisterToken(String token) => _api.unregisterToken(token);

  static String _messageFor(Object error) {
    if (error is ApiException) return error.message;
    return 'No se pudieron cargar las notificaciones.';
  }
}
