# RiceMap24 step9.58-owner-login-session-fix

Minimal fix based on step9.57.

## Fixed

1. Owner login compatibility for old staging users
   - Backend now accepts the same minimum password length as the registration UI: 6 characters.
   - Added a migration fallback for older owner records where the kitchen/listing exists, but `app_users` was not created or linked correctly.
   - If normal login fails, the backend checks the matching listing payload by exact email + password, creates/repairs the owner `app_users` record, links it to the listing, and then continues with normal cookie/session login.
   - Future logins then use the normal hashed-password session path.

2. New kitchen default images removed
   - Registration no longer creates a new kitchen with `assets/hero_fusion.jpg` as default hero image.
   - Registration no longer creates a default `Signature dish` with `assets/dish_adobo.jpg`.
   - New kitchens start with empty images/menu and should only show images the owner adds later.

## Not changed

- No new Render service.
- No new database.
- No Stripe changes.
- No email/password reset setup yet.
- No upload/image optimization changes yet.
- Scheduled deletion/restore logic is left as already implemented in 9.57.

## Test checklist after deploy

1. Deploy to existing Render service: `ricemap24-staging`.
2. Open `/health` and confirm PostgreSQL/disk status still looks correct.
3. Try login with a newly created owner account.
4. Try login with the older staging owner account that previously showed `Request failed`.
5. After login, go to Explore kitchens and confirm:
   - `My dashboard` is visible.
   - `Log out` is visible.
   - `Log in` is hidden.
   - `Register kitchen` is hidden.
6. Log out and confirm:
   - `Log in` is visible.
   - `Register kitchen` is visible.
   - `My dashboard` is hidden.
   - `Log out` is hidden.
7. Register a new kitchen and confirm it does not contain default food/hero images.
