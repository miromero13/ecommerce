# CU24 – Push notifications

## Objective

Implement the Android scope of CU24: persist user notifications, register Android device tokens, deliver push notifications through Firebase Cloud Messaging, show the in-app notification history, mark notifications as read, and route notification taps to the related mobile section.

## Problem

The repository has no notification/device-token persistence, API, mobile inbox, or push provider integration. Relevant business events are emitted from several backend service boundaries rather than one HTTP route.

## Why

Administrators, customers, and branch managers need timely alerts without manually polling the system, while notification history and read state must remain available in the mobile app.

## Authorized scope

- Backend notification and device-token infrastructure.
- Android FCM integration in the Flutter application.
- Mobile notification inbox, unread badge, read state, token registration, and tap routing.
- Notification emission for the currently supported reservation, order, and low-stock event paths.
- Additive schema only; do not change existing table attributes unless required for integration.
- Android-only was the initial delivery. Firebase Web Push is now authorized as the next slice; iOS remains out of scope.
- Preserve unrelated worktree changes. Do not modify the existing virtual try-on HTML.

## Constraints

- Use the existing FastAPI, SQLAlchemy, Alembic, and Flutter patterns.
- Use Firebase Admin SDK on the backend and `firebase_core`/`firebase_messaging` on Flutter.
- Keep the Firebase service-account file out of version control.
- Push delivery failures must not interrupt the originating business use case.
- Keep notification persistence provider-neutral so delivery can be retried or inspected.

## Tasks

- [x] T1 — Secure local FCM configuration and Android Gradle/Firebase initialization (Android-only; the supplied local config package mismatch remains an explicit build gap).
- [x] T2 — Add additive notification/device-token models, migration, schemas, service, and authenticated API endpoints.
- [x] T3 — Add safe notification emission and FCM delivery at service boundaries for reservation, order, and low-stock events.
- [x] T4 — Add Flutter FCM initialization, Android permission/token registration, foreground/background handling, and tap routing.
- [x] T5 — Add the mobile inbox, unread badge, read action, and focused tests.
- [x] T6 — Run focused and baseline checks, reconcile failures, update this document, and record work-unit commit evidence.
- [x] T7 — Add Firebase Web Messaging to Angular, register web tokens, and serve the messaging service worker.
- [x] T8 — Add the web notification inbox, unread badge, read action, permission handling, and data-driven tap navigation.
- [x] T9 — Run web-focused checks and record the combined Android/Web verification state.

## Acceptance criteria

- An authenticated Android user can register and refresh an FCM token without duplicate token rows.
- The authenticated user can list notifications, see unread count, mark one read, and open the related destination.
- A persisted notification is created before or alongside a push attempt; push failure is recorded and does not abort the source use case.
- Backend role and ownership checks prevent reading or marking another user's notifications.
- Reservation, order, and low-stock transitions reach the notification service through service-level paths, including non-HTTP paths where applicable.
- Android foreground, background, and notification-tap paths are covered by the smallest useful automated checks available in the repository.
- A supported HTTPS browser can request permission, register a web FCM token, receive foreground/background notifications, and open the related route.
- No existing table attributes are changed unnecessarily and no secret file is tracked.

## Applicable checks

```text
fvm flutter pub get (mobile)
fvm flutter analyze (mobile)
fvm flutter test mobile/test
python -m pytest -q backend/tests
npm --prefix frontend test (baseline only; frontend is out of initial scope)
git diff --check
git status --short
```

## Route and progress

- Route: delegated direct implementation; exploration was delegated because the flow spans backend, frontend, and mobile.
- TDD mode: not configured for this ODD task; use existing focused tests and functional checks.
- Delivery strategy: ask-on-risk; decide chaining only if the accumulated authored diff approaches the repository's review budget.
- Feature branch: required before the first work-unit commit because the current branch is `main`.
- Progress: backend notification persistence/API, FCM provider boundary, service-level event hooks, Android Firebase setup, and the Flutter inbox are complete. Firebase files were inspected only for metadata; the supplied Android config package is `com.example.flutter_template`, while the app application ID is `com.example.mobile`, so the Android build integration preserves that mismatch as an explicit gap rather than changing the existing app identity. Web Push configuration is supplied and is the active implementation slice.

## Work-unit evidence

- Backend and mobile implementation work units: complete; baseline reconciliation is recorded below.
- Dependency verification: `cd mobile && fvm flutter pub get` passes; Firebase dependency resolution temporarily changes the tracked iOS `Package.resolved`, which was reverted to preserve the Android-only scope.
- Focused backend verification: `PYTHONPATH=. .venv/bin/python -m pytest -q tests` → `63 passed, 2 warnings`.
- Focused mobile verification: `fvm flutter test test/notification_test.dart test/app_smoke_test.dart` → `6 passed`; targeted CU24 analyze → `No issues found`.
- Migration verification: Alembic script inspection → head `0037`.
- Work-unit commit: `b255b39 feat(backend): add notification history and FCM infrastructure` (API, additive migration, Firebase Admin boundary, delivery isolation tests).
- Work-unit commit: `71c5a3b feat(backend): emit notifications from business services` (reservation, order, sale, and low-stock service hooks).
- Mobile work-unit commit: `fb5ff81 feat(mobile): add Android notification inbox and FCM lifecycle` (Android Gradle/manifest setup, FlutterFire lifecycle wiring, inbox/controller, unread badge, safe tap routing, and focused tests).
- Baseline observations: the required root-level `python -m pytest -q backend/tests` cannot start because the system Python has no pytest and the repository expects the backend environment; the equivalent backend-venv run passes with `63 passed, 2 warnings`. The required `fvm flutter test mobile/test` path cannot run from the repository root because Flutter requires a project pubspec; the equivalent `cd mobile && fvm flutter test test` completes with `72 passed, 8 failed`, retaining failures in orders/catalog/reservation/profile/product-detail tests. `fvm flutter analyze` reports 10 issues: 8 pre-existing infos and 2 errors in `test/orders_page_test.dart`; the known product-detail variant failure remains unrelated to CU24. `npm --prefix frontend test` passes.
- Security verification: `git check-ignore` confirms `backend/.secrets/` and `mobile/android/app/google-services.json` are ignored; neither secret file is included in the implementation diff.
- Rollback boundary: remove the CU24 notification files and matching config/router/Gradle/pubspec/manifest changes; revert migration `0037` to remove only the two additive tables. Existing tables, virtual try-on HTML, iOS project files, and frontend code remain outside the feature.
- Deferred semantics: recommendation/catalog push events remain deferred because no corresponding domain transition event exists in the current services.

### Web Push slice evidence

- Web work-unit commits: `ea74ff7 feat(backend): accept web notification tokens` and `432309c feat(web): add Firebase push notifications`.
- Exact changed files: `backend/app/schemas/notification_schema.py`, `backend/tests/test_notifications.py`, `frontend/package.json`, `frontend/package-lock.json`, `frontend/src/environments/environment.ts`, `frontend/public/firebase-messaging-sw.js`, `frontend/src/app/app.ts`, `frontend/src/app/app.routes.ts`, `frontend/src/app/core/layouts/app-shell.component.ts`, `frontend/src/app/core/layouts/app-shell.component.html`, `frontend/src/app/features/shared/models/notification.model.ts`, `frontend/src/app/features/shared/services/notification-api.service.ts`, `frontend/src/app/features/shared/services/notification-push.service.ts`, `frontend/src/app/features/shared/pages/notification-page.component.ts`, `frontend/src/app/features/shared/pages/notification-page.component.html`, and this task document.
- `npm --prefix frontend install` → blocked by the pre-existing `angular-chrts@0.1.0-beta.7` peer requirement for Angular 19 while the project uses Angular 21 (`ERESOLVE`). `npm --prefix frontend install firebase --legacy-peer-deps` → dependency and lockfile update completed; npm reported 75 audit vulnerabilities.
- `npm --prefix frontend test` → Angular development build passed.
- `npm --prefix frontend run build` → production build passed with the existing initial bundle budget warning (`762.09 kB`, `12.09 kB` over `750 kB`). Built asset `frontend/dist/frontend/browser/firebase-messaging-sw.js` is present; `node --check frontend/public/firebase-messaging-sw.js` passed.
- `PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_notifications.py` from `backend` → `4 passed, 1 warning`.
- `git diff --check` → passed. `git status --short` confirms the unrelated pre-existing `mobile/ios/Runner.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved` remains modified and is not part of this slice.
- Browser delivery status: no browser/device push session was available, so real permission, FCM delivery, background display, and click routing remain pending manual HTTPS-browser verification.
- Current Android package mismatch gap remains unchanged: supplied local Firebase Android configuration is for `com.example.flutter_template`, while the app application ID is `com.example.mobile`; the existing Android integration preserves this as an explicit gap.
- Rollback boundary: revert the web-only files listed above, remove the `firebase` dependency and lockfile entries, and restore `DeviceTokenUpsert.platform` to `android`-only. Leave migration `0037`, Android notification behavior, existing tables, `mobile/ios/.../Package.resolved`, service-account files, `google-services.json`, and virtual try-on HTML untouched.
