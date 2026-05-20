# Step 9.63 — Auth login PostgreSQL date fix

Minimal fix after Step 9.62 still showed `Request failed (500)` on admin/owner login.

## Actual likely cause found in code

`recent_failed_login_count()` used SQLite-only SQL:

```sql
created_at >= datetime('now', ?)
```

with a parameter such as `-15 minutes`. This works in SQLite, but fails in PostgreSQL because PostgreSQL does not support SQLite's `datetime()` modifier syntax.

That function runs before credential checking for both owner login and admin login. Therefore login could fail with HTTP 500 even when the admin reset itself had worked.

## Fix

The cutoff time is now calculated in Python and passed as a normal SQL parameter:

```sql
created_at >= ?
```

This stays compatible with the project's SQLite/PostgreSQL wrapper.

## Test after deploy

1. Open `/health` and confirm new release/version if visible.
2. Open `/admin`.
3. Press **Reset local admin** with desired email/password and confirm `RESET`.
4. Then press **Log in** with the same credentials.
5. Test owner login with a newly registered kitchen.
6. If admin opens, use admin cleanup tools to hide/delete old test kitchens.

This step does not create any Render service, database, Stripe setup or email setup.
