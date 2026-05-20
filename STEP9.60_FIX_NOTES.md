# RiceMap24 step9.60-admin-login-map-cleanup-fix

Minimal fix after step 9.59.

## Fixes

1. Admin reset/login recovery
- Keeps the reset-local-admin button available on non-production admin login screens.
- Allows the reset endpoint on Render staging even if the service was accidentally marked with production env, but only when Render service/URL contains `staging`.
- Does not create a new Render service or database.
- Does not delete kitchens, owners, images or data.

2. Map/geocoding for new kitchens and location search
- Converts country names such as `Norway`, `United States`, `Sweden`, etc. to ISO2 before using Nominatim.
- This fixes a likely cause of new kitchens missing coordinates.
- Adds a small city fallback for common cities so staging does not depend fully on external geocoding.

3. Demo/test seed guard
- Removes the automatic staging seed condition.
- Demo kitchens are now seeded only when `ENABLE_DEMO_SEED` explicitly allows it.
- Existing demo/test kitchens are not deleted by this update; use admin after reset to hide/delete/clean them.

## Test after deploy

1. Open `/health` and confirm version:
`step9.60-admin-login-map-cleanup-fix`

2. Open `/admin`.
- Fill in the desired admin email and password.
- Click `Reset local admin` / `Nullstill lokal admin`.
- Confirm with `RESET`.
- Log in.

3. Clean old test kitchens from admin.

4. Register a new test kitchen with city/country.
- Complete staging checkout bypass.
- Confirm the kitchen appears on Explore.
- Confirm map/nearest search places it in the right area.

