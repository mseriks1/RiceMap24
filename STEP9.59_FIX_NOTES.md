# RiceMap24 step9.59-admin-reset-map-geocode-fix

Minimal fix after step9.58.

## Fixed

1. Admin recovery for staging/local
   - Added non-production `/api/auth/dev-reset-admin`.
   - The Admin login screen can show **Reset local admin** when an admin user already exists but old credentials fail.
   - This resets only app_users with role `admin` and admin sessions. It does not delete kitchens, owner users, images, support tickets or settings.

2. New kitchen map visibility
   - New draft creation now tries best-effort geocoding from postcode/city/area/country.
   - Coordinates are stored in `listings.lat`, `listings.lng` and `data_json`.
   - Staging checkout-bypass activation also retries geocoding.
   - Signup still succeeds if geocoding is unavailable.

3. Password length consistency
   - Frontend registration validation now matches backend: minimum 6 characters.

## Test after deploy

1. Open `/health` and confirm the release version is `step9.59-admin-reset-map-geocode-fix`.
2. Open `/admin`.
3. If old admin login fails, enter the new admin email/password, click **Reset local admin**, type `RESET`, then log in.
4. Use Admin to hide/deactivate/delete old test kitchens as needed.
5. Register a new kitchen with city/country.
6. Confirm it appears in Explore after staging bypass/activation.
7. Test location search/nearest again.

## Not changed

- No new Render service.
- No new database.
- No Stripe setup.
- No email/password reset.
- No automatic image optimization yet.
