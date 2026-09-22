# Foreground Push Notifications

## Objective
Show a visible Android notification when an FCM message arrives while the Flutter app is open.

## Problem
The backend completes the order-ready flow, persists the notification, and resolves the customer's device token. The mobile foreground handler only reloads the inbox, so Android displays no system notification while the app is active.

## Authorized Scope
- `mobile/pubspec.yaml` and its lockfile
- `mobile/lib/features/notifications/notification_push_service.dart`
- `mobile/lib/app/app.dart` only if callback wiring must change
- Focused mobile notification tests where practical

## Tasks
- [x] FPN-1 Add the existing-standard Flutter local notification dependency and initialize an Android channel.
- [ ] FPN-2 Display foreground FCM title/body/payload while preserving inbox refresh and tap behavior.
- [ ] FPN-3 Run formatting, analysis, focused tests, and a debug build; record evidence.

## Acceptance Criteria
- A foreground FCM message produces a visible high-priority Android notification.
- Notification title/body come from the FCM notification payload, with safe fallbacks.
- Existing token registration, inbox refresh, background handling, and tap routing remain intact.
- Android 13+ notification permission remains respected.

## Checks
- `flutter format --set-exit-if-changed lib test`
- `flutter analyze`
- `flutter test test/notification_test.dart`
- `flutter build apk --debug`

## Progress
- Route: delegated direct writer; two non-trivial mobile files plus dependency metadata.
- Current evidence: backend returned `200` for `/ready`, inserted notification `0cb10878-be20-4a0a-9cde-db2223fd5d10`, selected an active device token, and produced no FCM error. The app was foregrounded and refreshed `/api/notifications`.
- Observed verification: `dart format --output=none --set-exit-if-changed lib/features/notifications/notification_push_service.dart`, focused notification analysis, and `flutter test test/notification_test.dart` passed. The requested `flutter format` command is not available in Flutter 3.44; Dart format was used for the equivalent check.
- Limitation: `flutter analyze` still reports two pre-existing errors in `test/orders_page_test.dart`; `flutter build apk --debug` is blocked because `flutter_local_notifications` requires Android core-library desugaring, which is outside the authorized file scope.
