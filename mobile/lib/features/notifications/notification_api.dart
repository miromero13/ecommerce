import '../../core/network/api_client.dart';
import 'notification_models.dart';

class NotificationApi {
  NotificationApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<NotificationListResult> list() async {
    final response = await _client.get<List<NotificationItem>>(
      'notifications',
      parser: (value) => _parseList(value),
    );
    return NotificationListResult(
      notifications: response.data ?? const [],
      message: response.message,
    );
  }

  Future<int> unreadCount() async {
    final response = await _client.get<Map<String, dynamic>>(
      'notifications/unread-count',
      parser: (value) => _asMap(value),
    );
    return (response.data?['count'] as num?)?.toInt() ?? 0;
  }

  Future<NotificationItem> markRead(String id) async {
    final response = await _client.patch<NotificationItem>(
      'notifications/$id/read',
      parser: (value) => NotificationItem.fromJson(_asMap(value)),
    );
    if (response.data == null) {
      throw const FormatException('Notificación vacía');
    }
    return response.data!;
  }

  Future<void> markAllRead() async {
    await _client.patch<Map<String, dynamic>>('notifications/read-all');
  }

  Future<void> registerToken(String token) async {
    await _client.post<Map<String, dynamic>>(
      'notifications/tokens',
      data: {'token': token, 'platform': 'android'},
    );
  }

  Future<void> unregisterToken(String token) async {
    await _client.delete<Map<String, dynamic>>(
      'notifications/tokens',
      data: {'token': token, 'platform': 'android'},
      parser: (value) => _asMap(value),
    );
  }

  static List<NotificationItem> _parseList(dynamic value) {
    if (value is! List) {
      throw const FormatException('Las notificaciones no son una lista');
    }
    return value
        .map((item) {
          if (item is! Map) {
            throw const FormatException('Una notificación es inválida');
          }
          return NotificationItem.fromJson(Map<String, dynamic>.from(item));
        })
        .toList(growable: false);
  }

  static Map<String, dynamic> _asMap(dynamic value) {
    if (value is! Map) {
      throw const FormatException('La respuesta de notificaciones es inválida');
    }
    return Map<String, dynamic>.from(value);
  }
}

class NotificationListResult {
  const NotificationListResult({
    required this.notifications,
    required this.message,
  });

  final List<NotificationItem> notifications;
  final String message;
}
