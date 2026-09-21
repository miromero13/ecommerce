import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

class NotificationPushService {
  NotificationPushService({this._messaging});

  FirebaseMessaging? _messaging;
  StreamSubscription<String>? _tokenSubscription;
  StreamSubscription<RemoteMessage>? _messageSubscription;
  StreamSubscription<RemoteMessage>? _tapSubscription;
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
      await messaging.requestPermission(alert: true, badge: true, sound: true);
      final token = await messaging.getToken();
      if (token != null && token.isNotEmpty) await onToken(token);
      _tokenSubscription = messaging.onTokenRefresh.listen(onToken);
      _messageSubscription = FirebaseMessaging.onMessage.listen(
        (_) => onForegroundMessage(),
      );
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
