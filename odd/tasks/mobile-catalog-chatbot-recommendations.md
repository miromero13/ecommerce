# Mobile catalog chatbot and recommendations

## Objective

Bring the frontend client's authenticated chatbot and the "Recomendaciones para ti" carousel to the Flutter mobile app, reusing the existing backend endpoints and preserving the current catalog/reservation flows.

## Problem

The Angular client already exposes chatbot conversation controls and collaborative recommendations, while the mobile catalog has neither. Mobile clients therefore miss the same personalized shopping experience.

## Scope

- Add mobile API models and calls matching the frontend contracts.
- Show branch-aware collaborative recommendations for authenticated clients in a horizontal carousel.
- Record product views without blocking normal catalog actions.
- Add a client-only floating chatbot control and conversation UI with send, retry, reset confirmation, and recommendation navigation.
- Preserve guest catalog access and existing product/reservation navigation.

## Constraints

- Reuse the existing `ApiClient`, `AuthController`, catalog models, product cards, dialog/bottom-sheet primitives, and routes where possible.
- Do not add dependencies.
- Do not modify unrelated backend, checkout, payment, profile, or reservation worktree changes.
- User requested no commit, push, or PR; leave changes uncommitted.
- Effective TDD mode: unknown because Flutter is unavailable in this environment; run static checks if possible and report unavailable Flutter checks honestly.

## Tasks

- [x] ODD-CHAT-1 — Added authenticated catalog/recommendation telemetry and chatbot API/model contracts. Route: delegated direct writer. Checks: static checks were limited by the unavailable Dart/Flutter SDK.
- [x] ODD-CHAT-2 — Added the authenticated recommendation carousel to the mobile catalog without changing guest behavior. Route: delegated direct writer. Checks: static checks were limited by the unavailable Dart/Flutter SDK.
- [x] ODD-CHAT-3 — Added the client-only chatbot control and conversation UI, including reset confirmation and recommendation product navigation. Route: delegated direct writer. Checks: static checks were limited by the unavailable Dart/Flutter SDK.

## Acceptance criteria

- Authenticated `cliente` users can see recommendations and open products from the carousel.
- Product view telemetry uses the same endpoint and payload shape as the frontend.
- Authenticated `cliente` users can open the chatbot, load history, send messages, retry failed sends, and delete the conversation after confirmation.
- Chatbot recommendation cards open the corresponding mobile product detail.
- Guests do not invoke authenticated recommendation/chatbot endpoints and do not see the chatbot control.
- Existing catalog search, cart, reservation, and product-detail flows remain intact.

## Progress

- Exploration complete; frontend endpoint contracts mapped.
- ODD-CHAT-1 through ODD-CHAT-3 implemented in one bounded writer pass.
- Guest access remains public-only; authenticated calls are created with the active cliente token provider.
- Fixed recommendation-card vertical overflow by increasing the carousel viewport and added a non-blocking horizontal swipe hint.

## Verification evidence

- `flutter` executable: unavailable in the environment; `flutter test` and `flutter analyze` were not run.
- `dart` executable: unavailable in the environment; Dart formatting/static analysis was not run.
- `git diff --check`: passed.
- `git diff --check` after the carousel fix: passed.
- No focused tests were added or fabricated because the Flutter test runner was unavailable.
- Native review: not completed; review mode is globally enabled, but the uncommitted worktree mixes prior changes and multiple untracked files, and the negotiated candidate became stale before its candidate-scoped decision could be recorded.

## Next step

Run `dart format`, `flutter analyze`, and focused mobile tests when the Flutter SDK is available; perform a runtime smoke check with an authenticated cliente and a guest session. Re-run native review from a clean, intentionally scoped candidate if review is required.
