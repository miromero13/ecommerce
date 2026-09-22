# Downloadable Sales Note

## Objective
Enable authorized customers to download a readable Spanish sales note for each completed order from checkout success and order history.

## Authorized Scope
- Frontend customer cart and orders views only.
- Reuse `downloadSimplePdf` directly; do not change it or add an abstraction.
- Do not modify backend, database, mobile, dependencies, or unrelated working-tree changes.

## Acceptance Criteria
- Each sales note includes the order identifier, date, payment status and method, pickup code when present, item rows, totals, and an order-id-based filename.
- The checkout success area and every customer order card expose an accessible, clear download action.
- `npm test` is run from `frontend/` and its observed outcome is recorded.

## Checks
- Focused runtime harness: N/A — the download is a browser-only action with no available authenticated browser harness.
- Verification command: `npm test` from `frontend/`.

## Route and Delegation Evidence
- Route: delegated direct; no remote access used.
- Delegation: direct delegation to the `explore` and `general` roles.

## Tasks
- [x] Integrate `downloadSimplePdf` directly in the customer components to generate the Spanish sales note from an `Order`.
- [x] Add the accessible download actions to checkout success and customer order cards; verify and record the work-unit commit.

## Tracking State
- Engram mirror: pending — both immediate and post-verification attempts were unavailable because multiple active runtime sessions match `ecommerce`.
- Verification evidence: `cd frontend && npm test` passed on 2026-09-22; `ng build --configuration development` completed in 3.847 seconds and wrote `frontend/dist/frontend`.
- Commit identity: `fbf99282dd09a3e92cd49afcbf2b26184bbe0702` (`feat(cliente): add downloadable sales notes`).
