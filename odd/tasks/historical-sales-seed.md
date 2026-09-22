# Historical Sales Seed

## Objective

Expand demo seed data to include at least 50 client users and at least 1,000 valid historical sales over the rolling 180-day window ending at seed execution time.

## Scope

- `backend/seed.py`
- A focused backend test only if necessary and practical
- This task record

Excluded: runtime behavior, migrations, dependencies, iOS files, and unrelated changes.

## Acceptance Criteria

- [x] Seeded clients total at least 50 while preserving recognizable demo identities and credentials.
- [x] Seeded sales total at least 1,000, with valid items, totals, cashier/branch data, and unique cash references.
- [x] Every sale timestamp is unique, timezone-aware, and within the rolling window from 180 days ago through seed execution time.
- [x] Extra historical sales do not decrement current inventory.
- [x] Seed verification asserts client and sale counts plus the timestamp-window invariant.
- [x] Backend tests and syntax validation pass.

## Task Checklist

- [x] Create task record and mirror it to Engram when session ownership permits.
- [x] Inspect seed flow, models, and existing verification.
- [x] Implement deterministic client and synthetic historical-sale seed data.
- [x] Extend verification; existing seed verification is the focused executable coverage.
- [x] Run verification, update observed evidence, and commit one work unit.

## Route / Trigger Evidence

- Trigger: execute `backend/seed.py` against the local development database.
- Flow to verify: `_seed_users` -> `_seed_sales` -> `_verify_seed`.

## Verification Command

```sh
cd backend && .venv/bin/python -m pytest
```

Syntax check:

```sh
cd backend && .venv/bin/python -m py_compile seed.py
```

## Progress

- 2026-09-22: `_seed_users` now creates 50 clients; existing demo clients and `Fashion123!` credentials remain unchanged.
- 2026-09-22: `_seed_sales` produces exactly 1,000 sales. Synthetic rows rotate across branches, branch-valid cashiers, and catalog variants; they create `Sale`/`SaleItem` records directly and do not mutate inventory.
- 2026-09-22: `_verify_seed` checks client and sale minima, unique cash references, branch/cashier consistency, unique timezone-aware timestamps, and the 180-day rolling window.
- 2026-09-22: Local `ecommerce_db` seeder run initially exposed an existing `payment_attempts -> orders` foreign-key reset dependency. Reset now removes payment attempts before orders. The subsequent seed run succeeded: 62 seeded users and 1,000 seeded sales.
- 2026-09-22: Post-seed database query observed 51 client users, 1,000 sales, 1,000 distinct cash references, and a timestamp range from `2026-03-26T05:31:03.925435-04:00` through `2026-09-22T05:29:03.925435-04:00`.
- 2026-09-22: `backend/.venv/bin/python -m py_compile seed.py` passed. `backend/.venv/bin/python -m pytest` passed: 64 tests, 2 pre-existing deprecation warnings.
- 2026-09-22: Work-unit commit: `feat(seed): add historical sales demo data`.
