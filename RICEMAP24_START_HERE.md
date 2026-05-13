# RiceMap24 step 9.36 — stable local start

This package is a stabilization step. It does not add new product features.

## What this step is for

1. Start the app locally in a repeatable way.
2. Keep user data outside the code folder.
3. Check that the main public pages and key API endpoints respond.
4. Make the environment variables clearer before web deployment.

## Recommended local data folder

Use one fixed data folder outside the versioned code folder:

```env
RICEMAP_DATA_DIR=/Users/marius/RiceMap24-data
```

With this setting, local SQLite, uploads and backups are kept here:

```text
/Users/marius/RiceMap24-data/ricemap24.sqlite3
/Users/marius/RiceMap24-data/uploads
/Users/marius/RiceMap24-data/backups
```

This means you can replace the app code folder without deleting uploaded images or the local database.

## Local start on Mac

From the `api` folder:

```bash
cd api
./start-local.command
```

The command uses:

```env
RICEMAP_ENV=development
RICEMAP_DATA_DIR=$HOME/RiceMap24-data
PORT=8091
```

Open:

```text
http://127.0.0.1:8091/
http://127.0.0.1:8091/list
http://127.0.0.1:8091/admin
http://127.0.0.1:8091/health
```

## Local smoke test

Start the app first. Then open a second Terminal window:

```bash
cd api
source .venv/bin/activate
python3 check-local.py
```

The test checks:

- `/health`
- `/`
- `/list`
- `/pricing`
- `/for-cooks`
- `/admin`
- `/api/cuisines`
- `/api/listings`
- local CSS and JS files

## Before replacing an old folder

Do not move user uploads manually unless you know which data folder is active.

Check `/health` and confirm:

```json
"persistent_data_dir_set": true
"user_data_outside_code_dir": true
"uploads_inside_code_dir": false
"database_inside_code_dir": false
```

If uploaded actor images are missing after switching version, the likely reason is that the older version stored files in an old `uploads` folder inside the old code folder. Copy those files into:

```text
/Users/marius/RiceMap24-data/uploads
```

## Production note

This is still not a full public launch configuration. Before public deployment, use `.env.production.example` and configure real values for:

- `RICEMAP_ENV=production`
- `RICEMAP_SESSION_SECRET`
- `CORS_ALLOWED_ORIGINS`
- `DATABASE_URL` or a persistent data/storage setup
- `RICEMAP_PUBLIC_BASE_URL`
- backups
- error monitoring
- Stripe keys and price IDs
- email provider/DNS

