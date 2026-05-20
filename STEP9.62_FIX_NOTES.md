# Step 9.62 – Admin reset hardening

Minimal fix after `/admin` reset returned `Request failed (500)`.

## Changed

- Reworked `reset_admin_app_users()` so it updates/repairs the chosen admin account instead of deleting admin users first.
- Revokes old admin sessions without deleting kitchens, owner users, listings, images or content.
- Makes the reset path safer for PostgreSQL staging databases with old/partial auth data.
- Prevents admin activity logging from breaking emergency admin reset if the log table/schema is old.
- Returns a clearer backend error detail if reset still fails.

## Test

1. Deploy to Render.
2. Open `/admin`.
3. Enter desired admin email and password.
4. Click `Reset local admin`.
5. Type `RESET`.
6. It should reset the admin user and then log in.

Commit message:

```text
Step 9.62: Harden staging admin reset
```
