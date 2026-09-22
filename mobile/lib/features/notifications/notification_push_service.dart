import 'dart:async';
import 'dart:convert';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

class NotificationPushService {
  NotificationPushService({this._messaging});

  static const _channel = AndroidNotificationChannel(
    'foreground_notifications',
    'Foreground notifications',
    description: 'Notifications received while the app is open.',
    importance: Importance.high,
  );

  FirebaseMessaging? _messaging;
  final _localNotifications = FlutterLocalNotificationsPlugin();
  StreamSubscription<String>? _tokenSubscription;
  StreamSubscription<RemoteMessage>? _messageSubscription;
  StreamSubscription<RemoteMessage>? _tapSubscription;
  int _notificationId = 0;
  bool _started = false;

  Future<void> start({
    required Future<void> Function(String token) onToken,
    required void Function(Map<String, String> data) onTap,
    required void Function() onForegroundMessage,
  }) async {
    if (_started) return;
    _started = true;
    try {
      final messaging = _messaging ??= FirebaseMessaging.instance;
      try {
        await _initializeLocalNotifications(onTap);
      } catch (_) {
        // A local-notification failure must not disable FCM token registration.
      }
      await messaging.requestPermission(alert: true, badge: true, sound: true);
      final token = await messaging.getToken();
      if (token != null && token.isNotEmpty) await onToken(token);
      _tokenSubscription = messaging.onTokenRefresh.listen(onToken);
      _messageSubscription = FirebaseMessaging.onMessage.listen((message) {
        unawaited(_showForegroundNotification(message));
        onForegroundMessage();
      });
      _tapSubscription = FirebaseMessaging.onMessageOpenedApp.listen(
        (message) =>
            onTap(message.data.map((key, value) => MapEntry(key, '$value'))),
      );
      final initialMessage = await messaging.getInitialMessage();
      if (initialMessage != null) {
        onTap(initialMessage.data.map((key, value) => MapEntry(key, '$value')));
      }
    } catch (_) {
      await stop();
    }
  }

  Future<void> _initializeLocalNotifications(
    void Function(Map<String, String> data) onTap,
  ) async {
    await _localNotifications.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(
          requestAlertPermission: false,
          requestBadgePermission: false,
          requestSoundPermission: false,
        ),
      ),
      onDidReceiveNotificationResponse: (response) {
        final payload = response.payload;
        if (payload == null || payload.isEmpty) {
          onTap(const {});
          return;
        }
        try {
          final decoded = jsonDecode(payload);
          if (decoded is Map) {
            onTap(decoded.map((key, value) => MapEntry('$key', '$value')));
          }
        } catch (_) {
          onTap(const {});
        }
      },
    );
    await _localNotifications
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >()
        ?.createNotificationChannel(_channel);
  }

  Future<void> _showForegroundNotification(RemoteMessage message) async {
    final title = _messageText(
      message.notification?.title ?? message.data['title']?.toString(),
      'Nueva notificación',
    );
    final body = _messageText(
      message.notification?.body ?? message.data['body']?.toString(),
      'Tienes una nueva notificación.',
    );
    try {
      await _localNotifications.show(
        id: ++_notificationId,
        title: title,
        body: body,
        notificationDetails: NotificationDetails(
          android: AndroidNotificationDetails(
            _channel.id,
            _channel.name,
            channelDescription: _channel.description,
            importance: Importance.high,
            priority: Priority.high,
          ),
        ),
        payload: jsonEncode(message.data),
      );
    } catch (_) {
      // Inbox refresh remains available if Android cannot show the notification.
    }
  }

  String _messageText(String? value, String fallback) {
    final text = value?.trim();
    return text == null || text.isEmpty ? fallback : text;
  }

  Future<void> stop() async {
    await _tokenSubscription?.cancel();
    await _messageSubscription?.cancel();
    await _tapSubscription?.cancel();
    _tokenSubscription = null;
    _messageSubscription = null;
    _tapSubscription = null;
    _started = false;
  }
}
