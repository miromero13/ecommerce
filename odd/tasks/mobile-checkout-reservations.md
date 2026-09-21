# Mobile checkout, profile layout, and reservations

## Objective

Fix the mobile profile edit overflow, make Stripe configuration explicit, move checkout out of the orders list, allow payment of pending orders, and expose garment reservation from product detail.

## Scope

- Flutter mobile profile edit layout and narrow-width form controls.
- Mobile Stripe configuration and runtime dart-defines.
- Dedicated mobile checkout/payment route.
- Payment action for customer orders whose fulfillment is still in preparation and payment is pending.
- Product-detail navigation into the existing reservation flow.
- Do not alter unrelated web/frontend changes or the user's `BACKEND_URL` choice.

## Tasks

- [x] MOB-1 Fix profile edit horizontal overflow and Stripe environment-key lookup.
- [x] MOB-2 Move cart checkout into a dedicated payment/checkout view.
- [x] MOB-3 Add payment of an existing pending order and expose its action in orders.
- [x] MOB-4 Add a reserve-garment action from product detail using existing reservation arguments.
- [x] MOB-5 Run focused mobile tests/analyzer and record limitations.
- [x] MOB-6 Replace bottom navigation with Catálogo, Gestiones, and Cuenta.
- [x] MOB-7 Add visible Catálogo shortcuts for Carrito and Reservas.
- [x] MOB-8 Add a Gestiones hub for Mis reservas and Mis pedidos.
- [x] MOB-9 Remove reservation creation from the reservations list and redesign it as a focused flow.
- [x] MOB-10 Redirect successful checkout to Mis pedidos with order details.
- [x] MOB-11 Open reservation creation from the catalog and preserve multiple selected garments (product detail adds to the draft and returns to the catalog).

## Authorized scope

The user explicitly authorized implementation in the mobile app and the backend endpoint required to pay an existing pending order. Preserve all unrelated working-tree changes.

## Verification

- `cd mobile && flutter test`
- `cd mobile && flutter analyze`
- Focused profile, order, reservation, product-detail, and routing tests when available.
- `git diff --check`

## Route

Delegated direct implementation. Mapping required 4+ files; each non-trivial task uses one bounded writer and focused checks.

## Progress

- Exploration complete: the profile action row and non-expanded dropdowns are overflow candidates; Stripe uses the publishable key as the environment name; reservation API/page already exist but product detail never passes `ReservationArguments`.
- MOB-1 complete: profile actions now use Flutter's responsive `OverflowBar`, the gender dropdown uses `isExpanded: true`, and Stripe reads `STRIPE_PUBLISHABLE_KEY` with an empty default. The focused profile test exercises a 280px surface and asserts no layout exception; the existing `BACKEND_URL` default was preserved.
- MOB-2 complete: checkout now lives at `/checkout`, cart navigation uses that route, and the dedicated page keeps branch, payment-method, cash, Stripe PaymentSheet, feedback, and loading behavior. Orders now only list, show details, and expose actions.
- MOB-3 complete: pending orders can open the same page in order-payment mode; the mobile API/controller call `/payments/stripe/orders/{order_id}`; the backend validates ownership and pending fulfillment/payment state, reuses an existing PaymentIntent, and creates one with the existing idempotency attempt when needed.
- MOB-4 complete: product detail now exposes `Reservar prenda` beside the cart action, preserving the selected variant and quantity in the existing `ReservationArguments` flow. Guest authentication remains handled by `ReservationsPage`, and the action is unavailable without an authenticated route/controller or selected variant.
- MOB-5 complete: `python -m compileall -q backend/app` and `git diff --check` pass. Flutter tests and `flutter analyze` could not run because the environment has no `flutter` executable; the focused tests remain available for a Flutter-enabled environment.
- Follow-up fix: simplified the conditional payment button child in `orders_page.dart` to avoid the malformed list/spread structure reported during hot restart; delimiter validation and `git diff --check` pass.
- New UX scope: the bottom navigation is Catálogo/Gestiones/Cuenta; Catálogo exposes Carrito and Reservas shortcuts; Gestiones exposes Mis reservas and Mis pedidos; reservation creation is separated from the list; successful checkout returns to Mis pedidos.
- MOB-6 complete: the shared shell now exposes exactly Catálogo, Gestiones, and Cuenta; management surfaces and reservations/orders use selected index 1, while cart keeps index 0 with a Carrito title.
- MOB-7 complete: the catalog shows responsive, labeled Carrito and Reservas shortcut buttons before search and filters.
- MOB-8 complete: the reservations route is list-only; ReservationArguments are consumed only by the dedicated creation route.
- MOB-9 complete: `/reservation-create` provides the preparation summary, branch/date selection, validation, feedback, and return to the created reservation detail.
- MOB-10 complete: successful cash checkout and successful Stripe PaymentSheet completion replace checkout with Mis pedidos and pass the order ID for automatic detail loading.
- Checks: `python -m compileall -q backend/app` — passed; `git diff --check` — passed; `cd mobile && flutter test test/order_controller_test.dart test/order_api_test.dart test/order_models_test.dart test/cart_page_test.dart test/app_smoke_test.dart` — not run because `flutter` is unavailable; `cd mobile && flutter test test/product_detail_page_test.dart test/reservations_page_test.dart test/app_smoke_test.dart` — not run because `flutter` is unavailable (`command not found`); `cd mobile && flutter analyze` — not run because `flutter` is unavailable (`command not found`).
- Limitation: Flutter tests and analyzer still need to be rerun in a Flutter-enabled environment; backend endpoint behavior was syntax-checked but not exercised against Stripe or a live database.
- Verification for MOB-6..MOB-10: `cd mobile && flutter test test/app_smoke_test.dart test/catalog_page_test.dart test/product_detail_page_test.dart test/reservations_page_test.dart test/orders_page_test.dart test/cart_page_test.dart` — not run: `zsh:1: command not found: flutter`; `cd mobile && flutter analyze` — not run: `zsh:1: command not found: flutter`; `git diff --check` — passed.
- MOB-11 scope: the catalog Reservas shortcut opens only the creation flow; the list remains exclusive to Gestiones/Mis reservas; users can return to the catalog and accumulate multiple reservation items before confirming.
- MOB-11 previous implementation was insufficient: Product detail still navigated directly into `/reservation-create`; it must return the accumulated draft to Catalog instead.
- MOB-11 complete: product detail now merges the selected variant into the incoming draft and pops `ReservationArguments`; Catalog owns the current session draft, feeds it into detail, shows add feedback, and only its top `Reservas` shortcut opens `/reservation-create`. Focused tests cover the returned draft, accumulated items, and creation-route arguments.
- MOB-11 verification: `cd mobile && flutter test test/catalog_page_test.dart test/product_detail_page_test.dart test/reservations_page_test.dart test/app_smoke_test.dart` — not run: `zsh:1: command not found: flutter`; `cd mobile && flutter analyze` — not run: `zsh:1: command not found: flutter`; `git diff --check` — passed.
- MOB-11 limitation: Flutter tests and analyzer require a Flutter-enabled environment; the updated focused tests were not executable here.
