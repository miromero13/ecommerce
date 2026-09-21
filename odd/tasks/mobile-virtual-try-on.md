# Mobile virtual try-on

## Objective

Embed the existing Decart/Lucy VTON page in the Flutter app and send the selected catalog variant image through a JavaScript bridge, without duplicating the WebRTC or camera implementation.

## Problem

The mobile product detail currently has no virtual try-on entry point. The working browser implementation already lives in `frontend/public/decart-try-on.html` and expects a `decart-try-on-config` window message containing the API key, garment image URL, and product name.

## Scope

- Add a configurable frontend URL and Decart API key through Dart defines.
- Add a full-screen Flutter WebView page for `/decart-try-on.html`.
- Send the selected variant image and product metadata after the page finishes loading.
- Add the entry button to `ProductDetailPage`.
- Add camera permissions required by the embedded browser page.

## Constraints

- Use `fvm` for Flutter commands.
- Reuse the existing HTML/SDK/WebRTC implementation; do not port Decart SDK code to Dart.
- Keep the selected variant as the source of the garment image, falling back to the product image only when necessary.
- No backend or frontend behavior changes are required.

## Tasks

- [x] ODD-TRYON-1 — Add WebView dependency and runtime configuration.
- [x] ODD-TRYON-2 — Implement the WebView page and JavaScript configuration bridge.
- [x] ODD-TRYON-3 — Add the product-detail entry point and platform permissions.
- [x] ODD-TRYON-4 — Run formatting, analysis, and focused widget tests.
- [x] ODD-TRYON-5 — Grant Android WebView camera requests without granting unrelated resources and improve DOMException diagnostics.
- [x] ODD-TRYON-6 — Request the native camera runtime permission before creating the WebView while retaining the Android camera-only WebView grant.
- [x] ODD-TRYON-7 — Keep the mobile Decart session alive and retry remote video playback after media metadata is ready.
- [x] ODD-TRYON-8 — Wait for an actual remote video frame before hiding the loading screen and report missing frames explicitly.
- [x] ODD-TRYON-9 — Remove the stale mobile API-key fallback and surface Decart SDK errors in the embedded page.

## Authorized scope

- `mobile/pubspec.yaml`
- `mobile/pubspec.lock`
- `mobile/lib/core/config/app_config.dart`
- `mobile/lib/features/catalog/product_detail_page.dart`
- `mobile/lib/features/catalog/virtual_try_on_page.dart`
- `mobile/android/app/src/main/AndroidManifest.xml`
- `mobile/ios/Runner/Info.plist`
- `mobile/test/product_detail_page_test.dart`
- `frontend/public/decart-try-on.html`
- `odd/tasks/mobile-virtual-try-on.md`

## Acceptance criteria

- Product detail exposes a virtual try-on action only when an image URL is available.
- The WebView loads the configurable frontend URL plus `decart-try-on.html`.
- After page load, Flutter sends `decart-try-on-config` using `window.postMessage` with the selected image URL and product name.
- Closing the page returns to product detail and the WebView is disposed.
- Android and iOS declare camera access.
- `fvm flutter analyze` and the focused product-detail tests pass, or failures are recorded honestly if the local toolchain/device is unavailable.

## Route and checks

- Route: delegated direct — implementation spans multiple non-trivial Dart/platform files; one writer will own the change.
- Required checks: `fvm dart format --set-exit-if-changed <changed Dart files>`, `fvm flutter analyze`, `fvm flutter test test/product_detail_page_test.dart` from `mobile`.
- Progress: native runtime-permission correction implemented; `permission_handler` was downgraded to the SDK 36-compatible `^12.0.1` constraint; the mobile Decart key now must be supplied with `DECART_API_KEY`; runtime validation found a Decart `Insufficient credits` server error caused by the stale mobile fallback.
- Verification evidence: `fvm flutter pub get` passed and resolved `permission_handler` 12.0.3 with `permission_handler_android` 13.0.1 (20 packages still have newer versions outside the current constraints). `fvm dart format --set-exit-if-changed lib/features/catalog/virtual_try_on_page.dart` passed with no changes. `fvm flutter analyze` exited 1 with the pre-existing `test/orders_page_test.dart:87` const errors and eight informational lint notices elsewhere; no diagnostics were reported in the changed WebView file. `fvm flutter test test/product_detail_page_test.dart` exited 1 with 3 tests passing and the pre-existing `M · Rojo · SKU-2` fixture assertion failing at line 182. After the dependency fix, `fvm flutter build apk --debug` passed and produced `build/app/outputs/flutter-apk/app-debug.apk`.
- Runtime harness: Android emulator validation completed. Logcat confirmed LiveKit connection, remote stream delivery, and `play()` success; an emulator screenshot also confirmed visible remote video frames after processing. The frontend now waits for `requestVideoFrameCallback` before declaring the video ready and reports when no frame arrives within 10 seconds.
- Delivery: no commit, push, or PR created per user instruction.
- Next step: run with `--dart-define=DECART_API_KEY=<same active key configured by the frontend>`, deploy the updated `frontend/public/decart-try-on.html`, and rerun the emulator flow.

## ODD-TRYON-7 evidence

- Logcat confirmed `connected`, then `generating`, `Stream IA recibido.`, and `Prenda enviada correctamente.`; camera, WebSocket, LiveKit, Decart generation, and the remote stream all succeeded.
- The stream then disconnected because `startResultTimer()` scheduled a `5000ms` timeout whose callback called `stopEverything()`.
- Flutter now sends `keepSessionActive: true`, so only the mobile WebView skips that timeout; browser/iframe configuration without the flag keeps the existing expiration behavior.

## ODD-TRYON-9 evidence

- Angular iframe sends `environment.decartApiKey`; Flutter WebView sent a different hardcoded fallback from `AppConfig`.
- Android Logcat showed `[DecartSDK] realtime connect: exhausted all retries` followed by `Error: Insufficient credits`; camera and WebView initialization were already successful.
- The mobile fallback was removed so builds cannot silently use an exhausted key. The HTML now displays Decart errors in the loading view instead of only logging them to Chromium.
