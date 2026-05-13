# RiceMap24 step 9.37 – staging, Stripe and email readiness

This build is still based on the stable 9.36 app. It does not add new customer features.

## What this step prepares

1. Render staging deployment with persistent disk at `/var/data`.
2. Database, uploads and backups kept outside replaceable code.
3. Health/readiness checks for writable uploads/backups.
4. Stripe test mode env structure.
5. Email provider env structure for Postmark/SMTP/SendGrid.

## Minimum staging env

Use Render or equivalent hosting with a persistent disk mounted at `/var/data`.

```env
RICEMAP_ENV=staging
RICEMAP_PUBLIC_BASE_URL=https://YOUR-STAGING-URL.onrender.com
CORS_ALLOWED_ORIGINS=https://YOUR-STAGING-URL.onrender.com
RICEMAP_SESSION_SECRET=GENERATE_A_LONG_RANDOM_SECRET
RICEMAP_DATA_DIR=/var/data
DATABASE_URL=sqlite:////var/data/ricemap24.sqlite3
RICEMAP_UPLOADS_DIR=/var/data/uploads
RICEMAP_BACKUP_DIR=/var/data/backups
ENABLE_DEMO_SEED=false
RICEMAP_ENABLE_LEGACY_ADMIN_KEY=false
RICEMAP_STRIPE_MODE=test
RICEMAP24_EMAIL_PROVIDER=manual
RICEMAP24_EMAIL_DELIVERY_ENABLED=false
```

## Critical staging test

1. Deploy app.
2. Open `/health`.
3. Confirm:
   - `env = staging`
   - `user_data_outside_code_dir = true`
   - `uploads_dir_writable = true`
   - `backup_dir_writable = true`
4. Create admin/login.
5. Create or edit one actor.
6. Upload image and save a dish.
7. Redeploy/restart.
8. Confirm the actor, dish and image still exist.

If step 8 passes, code and user content are separated correctly.

## Web smoke test

From the `api` folder:

```bash
python3 check-web.py https://YOUR-STAGING-URL.onrender.com
```

## Stripe later in test mode

Add these after staging is running:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC_MONTHLY_NOK=price_...
STRIPE_PRICE_BUSINESS_MONTHLY_NOK=price_...
STRIPE_PRICE_GROWTH_MONTHLY_NOK=price_...
STRIPE_PRICE_PRO_MONTHLY_NOK=price_...
```

## Email later

Start with manual queue-only mode. When DNS/provider is ready, switch for example to Postmark:

```env
RICEMAP24_EMAIL_PROVIDER=postmark
RICEMAP24_EMAIL_DELIVERY_ENABLED=true
RICEMAP24_POSTMARK_SERVER_TOKEN=...
RICEMAP24_EMAIL_FROM=no-reply@ricemap24.com
RICEMAP24_EMAIL_REPLY_TO=no-reply@ricemap24.com
RICEMAP24_ADMIN_NOTIFICATION_EMAIL=your-admin-email@example.com
RICEMAP24_EMAIL_DNS_VERIFIED=true
```
