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
- Android only for the initial delivery. No Firebase Web or iOS setup.
- Preserve unrelated worktree changes. Do not modify the existing virtual try-on HTML.

## Constraints

- Use the existing FastAPI, SQLAlchemy, Alembic, and Flutter patterns.
- Use Firebase Admin SDK on the backend and `firebase_core`/`firebase_messaging` on Flutter.
- Keep the Firebase service-account file out of version control.
- Push delivery failures must not interrupt the originating business use case.
- Keep notification persistence provider-neutral so delivery can be retried or inspected.

## Tasks

- [ ] T1 — Secure local FCM configuration and Android Gradle/Firebase initialization (backend path/ignore groundwork complete; Android Gradle/plugin work remains in the mobile work unit).
- [x] T2 — Add additive notification/device-token models, migration, schemas, service, and authenticated API endpoints.
- [x] T3 — Add safe notification emission and FCM delivery at service boundaries for reservation, order, and low-stock events.
- [ ] T4 — Add Flutter FCM initialization, Android permission/token registration, foreground/background handling, and tap routing.
- [ ] T5 — Add the mobile inbox, unread badge, read action, and focused tests.
- [ ] T6 — Run focused and baseline checks, reconcile failures, update this document, and record work-unit commit evidence.

## Acceptance criteria

- An authenticated Android user can register and refresh an FCM token without duplicate token rows.
- The authenticated user can list notifications, see unread count, mark one read, and open the related destination.
- A persisted notification is created before or alongside a push attempt; push failure is recorded and does not abort the source use case.
- Backend role and ownership checks prevent reading or marking another user's notifications.
- Reservation, order, and low-stock transitions reach the notification service through service-level paths, including non-HTTP paths where applicable.
- Android foreground, background, and notification-tap paths are covered by the smallest useful automated checks available in the repository.
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
- Progress: backend notification persistence/API, FCM provider boundary, and service-level event hooks are complete. Firebase files were inspected only for metadata; the supplied Android config package is `com.example.flutter_template`, while the app application ID is `com.example.mobile`, so the Android build integration must preserve that mismatch as an explicit gap rather than changing the existing app identity.

## Work-unit evidence

- Backend implementation work units: complete. Mobile implementation is the next work unit.
- Focused backend verification: `PYTHONPATH=. .venv/bin/python -m pytest -q tests` → `63 passed, 2 warnings`.
- Focused mobile verification: pending mobile work unit.
- Migration verification: Alembic script inspection → head `0037`.
- Work-unit commit: `b255b39 feat(backend): add notification history and FCM infrastructure` (API, additive migration, Firebase Admin boundary, delivery isolation tests).
- Baseline observations: the required root-level `python -m pytest -q backend/tests` cannot start because the system Python has no pytest and the repository expects the backend environment; the equivalent backend-venv run passes. The required `fvm flutter test mobile/test` path cannot run from the repository root because Flutter requires a project pubspec; the equivalent `cd mobile && fvm flutter test test` runs and retains existing failures in orders/catalog/reservation/profile/product-detail tests. `fvm flutter analyze` retains pre-existing errors in `test/orders_page_test.dart`; the known product-detail variant failure remains unrelated to CU24. `npm --prefix frontend test` passes with the existing build-oriented warnings.
- Security verification: `git check-ignore` confirms `backend/.secrets/` and `mobile/android/app/google-services.json` are ignored; neither secret file is included in the implementation diff.
- Rollback boundary: remove the CU24 notification files and matching config/router/Gradle/pubspec/manifest changes; revert migration `0037` to remove only the two additive tables. Existing tables, virtual try-on HTML, iOS project files, and frontend code remain outside the feature.
- Deferred semantics: recommendation/catalog push events remain deferred because no corresponding domain transition event exists in the current services.
