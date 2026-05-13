# RiceMap24 step 9.40 — production pre-launch

This step is not a feature step. It checks the operational conditions needed before real launch.

## Required before public launch

1. User data must stay outside replaceable code.
   - database outside code folder or external database
   - uploads outside code folder
   - backups outside code folder

2. Web environment must be staging or production.
   - `RICEMAP_ENV=staging` for staging
   - `RICEMAP_ENV=production` for live

3. Public URL must be HTTPS.
   - `RICEMAP_PUBLIC_BASE_URL=https://...`

4. Admin access must use session login.
   - set a long `RICEMAP_SESSION_SECRET`
   - disable legacy admin-key fallback outside local development

5. Demo seeding must be off for web launch.
   - `ENABLE_DEMO_SEED=0`

6. Stripe must be configured or intentionally disabled.
   - staging can use Stripe test mode
   - production should use live mode when payments are active

7. Email must be configured or intentionally kept in manual mode.
   - Postmark, SMTP or SendGrid can be used

8. Backups and monitoring must be acknowledged.
   - `RICEMAP_BACKUP_CONFIGURED=true`
   - `RICEMAP_ERROR_MONITORING_CONFIGURED=true`

## Check endpoints

- `/health`
- `/api/admin/production-readiness`
- `/api/admin/pilot-readiness`
- `/api/admin/prelaunch-readiness`

Use `/api/admin/prelaunch-readiness` as the final checklist before opening the app to real users.
