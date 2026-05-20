# Step 9.61 – Admin reset recovery fix

Minimal correction after step 9.60.

## Fixed

- Admin reset endpoint now also checks the actual request hostname, not only Render environment variables.
- This matters when a staging Render service accidentally has production-like environment settings or lacks a service-name hint.
- API error messages now include HTTP status instead of only showing `Request failed`.

## Test

1. Deploy to Render.
2. Open `/admin`.
3. Enter desired admin email and password.
4. Click **Reset local admin** — not **Log in** first.
5. Confirm with `RESET`.
6. The app should then log in automatically.

If it still fails, the message should now show a useful status such as `404`, `400`, or `500`.
