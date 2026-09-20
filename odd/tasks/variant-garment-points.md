# Variant garment points

## Objective
Persist garment calibration points on `product_variants` and make both frontend virtual try-on detectors reuse saved points, asking for calibration only when the selected variant has no points.

## Problem
Calibration currently lives only in browser `localStorage`. Variant responses do not carry points, so a saved calibration is not shared across browsers or users.

## Scope
- Add nullable JSON calibration points to `product_variants` through the model, migration, API read/update path, and frontend catalog types.
- Do not add or generate calibration points in `backend/seed.py`; the values will be supplied manually or through the calibration save action.
- Load points for the selected variant in both client product-detail and reservation try-on flows.
- Reuse saved points immediately; expose the existing calibration UI only when points are missing, and persist new points after a valid save.
- Preserve unrelated working-tree changes.

## Authorized scope
`backend/app/models/product_variant.py`, `backend/app/schemas/catalog_schema.py`, `backend/app/services/catalog_service.py`, `backend/app/routes/catalog_routes.py`, `backend/alembic/versions/`, `frontend/src/app/features/shared/models/catalog.model.ts`, `frontend/src/app/features/shared/services/catalog-api.service.ts`, the two detector components, the two client page templates/components, and focused tests.

## Tasks
- [x] ODD-1 Add nullable variant points persistence and API support.
- [x] ODD-2 Load, apply, and save variant points in both frontend try-on flows.
- [x] ODD-3 Add focused checks and verify no seed data contains the new attribute.

## Acceptance criteria
- A variant response includes `garment_points: null` or a validated point array.
- Existing non-null points are applied without requiring manual calibration.
- Missing points keep calibration available and clearly tell the user to place and save them.
- Saving valid calibration points persists them on the selected variant.
- Seeder code does not set the new attribute.
- Backend and frontend focused checks pass.

## Checks
- Backend focused tests for catalog serialization/update and migration/model behavior.
- `npm --prefix frontend run build`.
- `git diff --check`.

## Route evidence
- ODD-1: delegated direct — backend and API span multiple non-trivial files.
- ODD-2: delegated direct — shared component and page integration span multiple non-trivial files.
- ODD-3: delegated verification — behavior crosses backend/frontend boundaries.

## Progress
- Feature document created before source changes.
- ODD-1 through ODD-3 implemented in one bounded writer task.
- Backend focused test is blocked by the environment because `pytest` is unavailable; frontend build passes.
