from __future__ import annotations

import os
import shutil
import zipfile
import uuid
import csv
import json
import re
import math
import math
import time
import traceback
from string import Template
from datetime import datetime, timedelta
from io import BytesIO

import qrcode
from PIL import Image, ImageOps, ImageDraw

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
from typing import Optional

import httpx

import stripe

import smtplib
import ssl
from email.message import EmailMessage

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from .data import LISTINGS, CUISINES
from .config import runtime_config, is_development, is_staging, is_production
from .db import (
    init_db,
    seed_if_empty,
    list_listings as db_list_listings,
    get_by_slug,
    get_by_id,
    get_by_preview_token,
    create_draft,
    update_draft,
    request_activation,
    admin_list,
    admin_activate,
    admin_deactivate,
    admin_update_meta,
    ensure_plan,
    geocache_get,
    geocache_set,
    get_by_stripe_subscription_id,
    stripe_mark_checkout_session,
    stripe_mark_subscription_active,
    stripe_mark_inactive_by_subscription,
    set_listing_publication,
    soft_delete_listing_by_owner,
    restore_deleted_listing_by_admin,
    list_customers,
    create_customer,
    update_customer,
    delete_customer,
    list_transactions,
    get_transaction_by_id,
    create_transaction,
    delete_transaction,
    summarize_transactions,
    top_customers,
    top_dishes,
    set_listing_currency,
    create_receipt,
    list_receipts,
    get_receipt_by_id,
    get_receipt_by_public_token,
    set_receipt_email_status,
    log_supplier_click,
    create_support_ticket,
    list_support_tickets,
    get_support_ticket,
    add_support_ticket_message,
    update_support_ticket,
    refresh_billing_visibility,
    get_admin_settings,
    update_admin_settings,
    log_admin_activity,
    list_admin_activity_log,
    list_discount_codes,
    upsert_discount_code,
    set_discount_code_active,
    queue_admin_notification,
    list_admin_notifications,
    get_admin_notification,
    mark_admin_notification_status,
    queue_due_access_notifications,
    list_admin_users,
    upsert_admin_user,
    mark_admin_user_seen,
    create_admin_announcement,
    list_admin_announcements,
    set_admin_announcement_status,
    list_active_owner_announcements,
    create_app_user,
    get_app_user_by_email,
    recent_failed_login_count,
    record_login_attempt,
    authenticate_app_user,
    authenticate_or_migrate_legacy_owner,
    cleanup_expired_app_sessions,
    create_app_session,
    get_user_by_session_token,
    revoke_app_session,
    list_app_users,
    record_app_error_log,
    list_app_error_logs,
    cleanup_app_error_logs,
    connect,
    set_listing_coordinates,
    reset_admin_app_users,
)

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(runtime_config.uploads_dir).resolve()
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

WEB_PUBLIC = (BASE_DIR / ".." / ".." / "web" / "public").resolve()


# --- Recipe library (markdown) ---------------------------------------------
RECIPES_DIR = (BASE_DIR / "recipes_md").resolve()
RECIPES_DIR.mkdir(parents=True, exist_ok=True)

MASTERCLASS_DIR = (BASE_DIR / "masterclass_md").resolve()
MASTERCLASS_DIR.mkdir(parents=True, exist_ok=True)
MASTERCLASS_IMAGES_DIR = (WEB_PUBLIC / "masterclass_images").resolve()
MASTERCLASS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
MARKETING_COACH_DIR = (BASE_DIR / "marketing_coach_md").resolve()
MARKETING_COACH_DIR.mkdir(parents=True, exist_ok=True)
MARKETING_COACH_IMAGES_DIR = (WEB_PUBLIC / "marketing_coach_images").resolve()
MARKETING_COACH_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
BUSINESS_COACH_DIR = (BASE_DIR / "business_coach_md").resolve()
BUSINESS_COACH_DIR.mkdir(parents=True, exist_ok=True)
BUSINESS_COACH_IMAGES_DIR = (WEB_PUBLIC / "business_coach_images").resolve()
BUSINESS_COACH_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

INDEX_HTML = WEB_PUBLIC / "index.html"

app = FastAPI(title="RiceMap24 MVP", version=runtime_config.release_version)


def _request_meta(request: Request) -> dict:
    try:
        ip = request.client.host if request.client else ""
    except Exception:
        ip = ""
    return {
        "path": str(request.url.path or "")[:240],
        "method": str(request.method or "")[:20],
        "ip": ip[:80],
        "user_agent": (request.headers.get("user-agent") or "")[:400],
        "request_id": (request.headers.get("x-request-id") or str(uuid.uuid4()))[:80],
    }


def _monitoring_config_snapshot() -> dict:
    return {
        "error_monitoring_configured": bool(runtime_config.error_monitoring_configured),
        "error_log_configured": bool(runtime_config.error_log_configured),
        "request_logging_enabled": bool(runtime_config.request_logging_enabled),
        "log_level": runtime_config.log_level,
        "retention_days": runtime_config.error_log_retention_days,
        "development_defaults_enabled": bool(is_development()),
        "ready_for_production": bool(runtime_config.error_monitoring_configured and runtime_config.error_log_configured),
        "external_monitoring_note": "Set RICEMAP_ERROR_MONITORING_CONFIGURED=true only after external monitoring/log alerts are configured.",
    }


@app.middleware("http")
async def request_and_error_monitoring(request: Request, call_next):
    meta = _request_meta(request)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if runtime_config.request_logging_enabled and request.url.path.startswith("/api") and int(getattr(response, "status_code", 200) or 200) >= 500:
            try:
                record_app_error_log(
                    level="warning",
                    source="backend",
                    path=meta["path"],
                    method=meta["method"],
                    status_code=int(response.status_code),
                    message=f"HTTP {response.status_code}",
                    request_id=meta["request_id"],
                    ip=meta["ip"],
                    user_agent=meta["user_agent"],
                    details={"duration_ms": duration_ms},
                )
            except Exception:
                pass
        response.headers["X-Request-ID"] = meta["request_id"]
        return response
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        try:
            record_app_error_log(
                level="error",
                source="backend",
                path=meta["path"],
                method=meta["method"],
                status_code=500,
                message=str(exc)[:500],
                traceback_text=traceback.format_exc(),
                request_id=meta["request_id"],
                ip=meta["ip"],
                user_agent=meta["user_agent"],
                details={"duration_ms": duration_ms},
            )
        except Exception:
            pass
        raise


@app.post("/api/supplier-click")
async def api_supplier_click(request: Request):
    """Lightweight analytics endpoint for partner/supplier links.

    Called from the Owner Dashboard when a kitchen clicks a supplier link.
    We validate by preview_token to avoid random spam.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    token = (payload or {}).get("token") or ""
    supplier = (payload or {}).get("supplier") or {}
    region = (payload or {}).get("region") or supplier.get("region") or ""

    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    # We prefer preview_token validation, but some pages (e.g. /r/amazon)
    # may receive the kitchen slug in the "t" query param. Accept slug as
    # a safe fallback to avoid breaking UX while still keeping this endpoint
    # non-public (requires a real listing).
    listing = get_by_preview_token(str(token))
    if not listing:
        listing = get_by_slug(str(token))
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    supplier_id = str(supplier.get("id") or supplier.get("name") or "")[:80]
    supplier_name = str(supplier.get("name") or "")[:200]
    url = str(supplier.get("url") or "")[:500]

    # request metadata
    ip = ""
    try:
        ip = request.client.host if request.client else ""
    except Exception:
        ip = ""
    user_agent = request.headers.get("user-agent", "")[:400]
    referer = request.headers.get("referer", "")[:400]

    meta = {
        "lang": (payload or {}).get("lang"),
        "page": (payload or {}).get("page"),
    }

    # Persist (best-effort)
    try:
        log_supplier_click(
            listing_id=int(listing["id"]),
            region=str(region),
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            url=url,
            ip=ip,
            user_agent=user_agent,
            referer=referer,
            meta=meta,
        )
    except Exception:
        # never block the click
        pass

    return {"ok": True}


class NoCacheStaticFiles(StaticFiles):
    """StaticFiles that disables caching (dev convenience).

    This prevents stale /app.js issues when iterating quickly and
    avoids confusing blank-page failures caused by cached syntax errors.
    """

    async def get_response(self, path: str, scope):  # type: ignore[override]
        response = await super().get_response(path, scope)
        if is_development():
            response.headers["Cache-Control"] = "no-store"
        return response


# CORS is open only in local development. Staging/production must define
# CORS_ALLOWED_ORIGINS, e.g. https://staging.ricemap24.com,https://ricemap24.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=runtime_config.safe_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Baseline browser security headers.

    Kept conservative for the current MVP so local tools and previews keep working.
    HTTPS enforcement is delegated to the production host/proxy, but production
    readiness now checks that the public base URL is HTTPS.
    """
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(self)")
    if is_production() or runtime_config.require_https:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response

ADMIN_KEY = runtime_config.admin_key

SESSION_COOKIE_NAME = "ricemap24_session"


def _request_ip(request: Request) -> str:
    try:
        return request.client.host if request.client else ""
    except Exception:
        return ""


def _session_cookie_kwargs() -> dict:
    return {
        "httponly": True,
        "secure": not is_development(),
        "samesite": "lax",
        "path": "/",
        "max_age": int(runtime_config.session_days) * 24 * 60 * 60,
    }


def _current_user_from_request(request: Request) -> Optional[dict]:
    token = request.cookies.get(SESSION_COOKIE_NAME) or ""
    if not token:
        auth = request.headers.get("authorization") or ""
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
    if not token:
        return None
    return get_user_by_session_token(token)


def _require_session_user(request: Request, *, roles: Optional[set[str]] = None) -> dict:
    user = _current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    if roles and user.get("role") not in roles:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


def _admin_authorized(request: Optional[Request] = None, key: Optional[str] = None) -> bool:
    # Session auth is the normal admin path. The old admin key is kept only as a
    # non-production development fallback while the admin area is being finished.
    if request is not None:
        user = _current_user_from_request(request)
        if user and user.get("role") == "admin":
            return True
    if runtime_config.legacy_admin_key_available and key and key == ADMIN_KEY:
        return True
    return False


# Stripe (subscriptions)
STRIPE_MODE = runtime_config.stripe_mode
STRIPE_SECRET_KEY = (
    os.environ.get("STRIPE_SECRET_KEY", "")
    or os.environ.get(f"STRIPE_SECRET_KEY_{STRIPE_MODE.upper()}", "")
)
STRIPE_WEBHOOK_SECRET = (
    os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    or os.environ.get(f"STRIPE_WEBHOOK_SECRET_{STRIPE_MODE.upper()}", "")
)

# Markets supported by pricing UI. Stripe price ids can be configured per currency:
# STRIPE_PRICE_BASIC_MONTHLY_NOK=price_...
STRIPE_CURRENCY_MARKETS = ("NOK", "SEK", "DKK", "EUR", "GBP", "USD", "CHF")
STRIPE_COUNTRY_CURRENCY = {
    "NO": "NOK", "SE": "SEK", "DK": "DKK", "FI": "EUR", "DE": "EUR", "FR": "EUR",
    "ES": "EUR", "NL": "EUR", "PT": "EUR", "IT": "EUR", "IE": "EUR", "AT": "EUR",
    "BE": "EUR", "GB": "GBP", "UK": "GBP", "US": "USD", "CH": "CHF",
}
STRIPE_PLAN_KEYS = ("basic", "business", "growth", "pro")
STRIPE_BILLING_KEYS = ("monthly", "yearly")

# Legacy/global Price IDs are still supported while Stripe is being wired up.
STRIPE_PRICE_BASIC_MONTHLY = os.environ.get("STRIPE_PRICE_BASIC_MONTHLY", "")
STRIPE_PRICE_BASIC_YEARLY = os.environ.get("STRIPE_PRICE_BASIC_YEARLY", "")
STRIPE_PRICE_PREMIUM_MONTHLY = os.environ.get("STRIPE_PRICE_PREMIUM_MONTHLY", "")  # legacy Business
STRIPE_PRICE_PREMIUM_YEARLY = os.environ.get("STRIPE_PRICE_PREMIUM_YEARLY", "")    # legacy Business
STRIPE_PRICE_BUSINESS_MONTHLY = os.environ.get("STRIPE_PRICE_BUSINESS_MONTHLY", STRIPE_PRICE_PREMIUM_MONTHLY)
STRIPE_PRICE_BUSINESS_YEARLY = os.environ.get("STRIPE_PRICE_BUSINESS_YEARLY", STRIPE_PRICE_PREMIUM_YEARLY)
STRIPE_PRICE_PLUS_MONTHLY = os.environ.get("STRIPE_PRICE_PLUS_MONTHLY", "")        # legacy Growth
STRIPE_PRICE_PLUS_YEARLY = os.environ.get("STRIPE_PRICE_PLUS_YEARLY", "")          # legacy Growth
STRIPE_PRICE_GROWTH_MONTHLY = os.environ.get("STRIPE_PRICE_GROWTH_MONTHLY", STRIPE_PRICE_PLUS_MONTHLY)
STRIPE_PRICE_GROWTH_YEARLY = os.environ.get("STRIPE_PRICE_GROWTH_YEARLY", STRIPE_PRICE_PLUS_YEARLY)
STRIPE_PRICE_PRO_MONTHLY = os.environ.get("STRIPE_PRICE_PRO_MONTHLY", "")
STRIPE_PRICE_PRO_YEARLY = os.environ.get("STRIPE_PRICE_PRO_YEARLY", "")


def _stripe_global_price_ids() -> dict:
    return {
        "basic_monthly": STRIPE_PRICE_BASIC_MONTHLY,
        "basic_yearly": STRIPE_PRICE_BASIC_YEARLY,
        "business_monthly": STRIPE_PRICE_BUSINESS_MONTHLY,
        "business_yearly": STRIPE_PRICE_BUSINESS_YEARLY,
        "growth_monthly": STRIPE_PRICE_GROWTH_MONTHLY,
        "growth_yearly": STRIPE_PRICE_GROWTH_YEARLY,
        "pro_monthly": STRIPE_PRICE_PRO_MONTHLY,
        "pro_yearly": STRIPE_PRICE_PRO_YEARLY,
    }


def _stripe_currency_price_id(plan: str, billing: str, currency: str) -> str:
    env_name = f"STRIPE_PRICE_{plan.upper()}_{billing.upper()}_{currency.upper()}"
    return os.environ.get(env_name, "").strip()


def _stripe_country_to_currency(country: str = "") -> str:
    c = str(country or "NO").upper().strip()
    return STRIPE_COUNTRY_CURRENCY.get(c, "NOK")


def _stripe_config_snapshot() -> dict:
    global_ids = _stripe_global_price_ids()
    configured_by_currency = {}
    missing_by_currency = {}
    for currency in STRIPE_CURRENCY_MARKETS:
        configured_by_currency[currency] = {}
        missing_by_currency[currency] = []
        for plan in STRIPE_PLAN_KEYS:
            for billing in STRIPE_BILLING_KEYS:
                key = f"{plan}_{billing}"
                ready = bool(_stripe_currency_price_id(plan, billing, currency) or global_ids.get(key))
                configured_by_currency[currency][key] = ready
                if not ready:
                    missing_by_currency[currency].append(f"STRIPE_PRICE_{plan.upper()}_{billing.upper()}_{currency}")
    all_ready = all(not v for v in missing_by_currency.values())
    return {
        "mode": STRIPE_MODE,
        "secret_key_set": bool(STRIPE_SECRET_KEY),
        "webhook_secret_set": bool(STRIPE_WEBHOOK_SECRET),
        "configured_by_currency": configured_by_currency,
        "missing_by_currency": missing_by_currency,
        "all_supported_currency_prices_ready": all_ready,
        "global_price_ids": {k: bool(v) for k, v in global_ids.items()},
    }


if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


def _production_readiness_snapshot() -> dict:
    """Small admin-facing production checklist status.

    This does not expose secret values. It only reports whether required
    production configuration appears to be present.
    """
    stripe_cfg = _stripe_config_snapshot()
    price_ids = _stripe_global_price_ids()
    email_settings = get_admin_settings()
    email_cfg = _email_config_snapshot(email_settings)
    provider = str(email_cfg.get("provider") or "manual").lower()
    email_ready = bool(email_cfg.get("ready_for_real_delivery")) or (is_development() and provider == "manual")
    checks = [
        {"id":"runtime_env", "label":"Runtime environment set", "ready":runtime_config.env in {"development", "staging", "production"}, "kind":"config", "env":runtime_config.env},
        {"id":"cors_origins", "label":"CORS origins configured for non-development", "ready":is_development() or bool(runtime_config.cors_allowed_origins), "kind":"security", "origins":runtime_config.cors_allowed_origins},
        {"id":"demo_seed_guard", "label":"Demo seeding disabled outside safe modes", "ready":(is_development() or (not runtime_config.enable_demo_seed and not runtime_config.allow_demo_seed)), "kind":"security", "enabled":bool(runtime_config.enable_demo_seed), "allowed":bool(runtime_config.allow_demo_seed)},
        {"id":"database_url", "label":"External DATABASE_URL configured for web environments", "ready":is_development() or bool(runtime_config.database_url), "kind":"database"},
        {"id":"user_data_outside_code", "label":"User data stored outside replaceable code", "ready":is_development() or bool(runtime_config.user_data_outside_code_dir), "kind":"storage", "details": _persistent_data_snapshot()},
        {"id":"upload_storage", "label":"Persistent upload storage configured", "ready":bool(runtime_config.uploads_dir), "kind":"storage", "mode":runtime_config.upload_storage_mode},
        {"id":"upload_storage_writable", "label":"Persistent uploads are writable", "ready":_directory_writable(runtime_config.uploads_dir), "kind":"storage"},
        {"id":"backup_storage_writable", "label":"Backup directory is writable", "ready":_directory_writable(runtime_config.backup_dir), "kind":"backup"},
        {"id":"https_public_url", "label":"HTTPS public base URL configured", "ready":is_development() or (bool(runtime_config.public_base_url) and runtime_config.public_base_url.startswith("https://")), "kind":"security", "url_set":bool(runtime_config.public_base_url)},
        {"id":"security_headers", "label":"Baseline security headers enabled", "ready":True, "kind":"security"},
        {"id":"session_secret", "label":"Long session secret configured", "ready":is_development() or bool(runtime_config.session_secret and len(runtime_config.session_secret) >= 32), "kind":"security"},
        {"id":"login_rate_limit", "label":"Login rate limiting enabled", "ready":True, "kind":"security", "max_failed":runtime_config.login_max_failed_attempts, "lockout_minutes":runtime_config.login_lockout_minutes},
        {"id":"backup_configured", "label":"Backup configured and acknowledged", "ready":is_development() or bool(runtime_config.backup_configured), "kind":"backup", "details": _backup_config_snapshot()},
        {"id":"error_monitoring", "label":"Error monitoring configured", "ready":is_development() or bool(runtime_config.error_monitoring_configured), "kind":"monitoring", "details": _monitoring_config_snapshot()},
        {"id":"stripe_mode", "label":"Stripe mode configured", "ready":STRIPE_MODE in {"disabled", "test", "live"}, "kind":"stripe", "mode":STRIPE_MODE},
        {"id":"stripe_secret", "label":"Stripe secret key", "ready":bool(STRIPE_SECRET_KEY) or STRIPE_MODE == "disabled", "kind":"stripe"},
        {"id":"stripe_webhook_secret", "label":"Stripe webhook secret", "ready":bool(STRIPE_WEBHOOK_SECRET) or STRIPE_MODE == "disabled", "kind":"stripe"},
        {"id":"stripe_price_ids", "label":"Stripe price IDs for supported currencies", "ready":bool(stripe_cfg.get("all_supported_currency_prices_ready")) or STRIPE_MODE == "disabled", "kind":"stripe", "missing_by_currency":stripe_cfg.get("missing_by_currency", {})},
        {"id":"admin_session_auth", "label":"Admin uses session login", "ready":(is_development() or not runtime_config.legacy_admin_key_available), "kind":"security", "legacy_key_fallback":bool(runtime_config.legacy_admin_key_available)},
        {"id":"email_provider", "label":"Email provider configured", "ready":email_ready, "kind":"email", "provider":provider, "delivery_enabled":email_cfg.get("delivery_enabled"), "missing":email_cfg.get("missing", [])},
        {"id":"deployment_provider", "label":"Deployment provider selected", "ready":is_development() or runtime_config.deployment_provider != "local", "kind":"deployment", "provider":runtime_config.deployment_provider},
        {"id":"deployment_region", "label":"Deployment region documented", "ready":is_development() or bool(runtime_config.deployment_region), "kind":"deployment", "region_set":bool(runtime_config.deployment_region)},
        {"id":"release_version", "label":"Release version exposed", "ready":bool(runtime_config.release_version), "kind":"deployment", "release_version":runtime_config.release_version},
    ]
    ready_count = sum(1 for c in checks if c.get("ready"))
    return {
        "checks": checks,
        "ready_count": ready_count,
        "total_count": len(checks),
        "mode": "production-ready" if ready_count == len(checks) else "local-mvp",
        "stripe": stripe_cfg,
        "price_ids": {k: bool(v) for k, v in price_ids.items()},
        "public_base_url_set": bool(runtime_config.public_base_url),
        "persistent_data": _persistent_data_snapshot(),
        "backup_configured": bool(runtime_config.backup_configured),
        "backup": _backup_config_snapshot(),
        "error_monitoring_configured": bool(runtime_config.error_monitoring_configured),
        "monitoring": _monitoring_config_snapshot(),
        "email": email_cfg,
        "deployment": _deployment_config_snapshot(),
    }



def _persistent_data_snapshot() -> dict:
    """Safe path-placement snapshot. Exposes booleans, not absolute server paths."""
    return {
        "persistent_data_dir_set": bool(runtime_config.persistent_data_dir_set),
        "database_inside_code_dir": bool(runtime_config.database_inside_code_dir),
        "uploads_inside_code_dir": bool(runtime_config.uploads_inside_code_dir),
        "backup_inside_code_dir": bool(runtime_config.backup_inside_code_dir),
        "uploads_dir_set": bool(runtime_config.uploads_dir),
        "backup_dir_set": bool(runtime_config.backup_dir),
        "database_engine": runtime_config.database_engine,
        "user_data_outside_code_dir": bool(runtime_config.user_data_outside_code_dir),
    }


def _deployment_config_snapshot() -> dict:
    """Safe deployment/runtime snapshot. Does not expose secret values."""
    try:
        pilot_snapshot = _pilot_readiness_snapshot()
    except Exception:
        pilot_snapshot = {"pilot_ready": False, "ready_count": 0, "total_count": 0}
    try:
        prelaunch_snapshot = _prelaunch_readiness_snapshot()
    except Exception:
        prelaunch_snapshot = {"prelaunch_ready": False, "ready_count": 0, "total_count": 0}
    return {
        "environment": runtime_config.env,
        "provider": runtime_config.deployment_provider,
        "region": runtime_config.deployment_region,
        "public_base_url_set": bool(runtime_config.public_base_url),
        "public_base_url_is_https": bool(runtime_config.public_base_url.startswith("https://")),
        "require_https": bool(runtime_config.require_https),
        "port": runtime_config.port,
        "release_version": runtime_config.release_version,
        "pilot_ready": bool(pilot_snapshot.get("pilot_ready")),
        "pilot_ready_count": pilot_snapshot.get("ready_count"),
        "pilot_total_count": pilot_snapshot.get("total_count"),
        "prelaunch_ready": bool(prelaunch_snapshot.get("prelaunch_ready")),
        "prelaunch_ready_count": prelaunch_snapshot.get("ready_count"),
        "prelaunch_total_count": prelaunch_snapshot.get("total_count"),
        "demo_seed_enabled": bool(runtime_config.enable_demo_seed),
        "demo_seed_allowed": bool(runtime_config.allow_demo_seed),
        "legacy_admin_key_available": bool(runtime_config.legacy_admin_key_available),
        "git_commit_set": bool(runtime_config.git_commit_sha),
        "database_engine": runtime_config.database_engine,
        "database_ssl": bool(runtime_config.database_ssl),
        "upload_storage_mode": runtime_config.upload_storage_mode,
        "backup_configured": bool(runtime_config.backup_configured),
        "backup": _backup_config_snapshot(),
        "error_monitoring_configured": bool(runtime_config.error_monitoring_configured),
    }




def _pilot_readiness_snapshot() -> dict:
    """Pilot-focused checklist for a small closed test before public launch.

    This is intentionally less strict than production readiness. It verifies that
    the app can run with a few real/test kitchens without losing data, and that
    payment/email are either configured for test use or explicitly kept safe.
    """
    email_cfg = _email_config_snapshot(get_admin_settings())
    stripe_cfg = _stripe_config_snapshot()
    try:
        all_items = db_list_listings(include_drafts=True)
    except Exception:
        all_items = []
    try:
        public_items = db_list_listings(include_drafts=False)
    except Exception:
        public_items = []
    plan_counts = {"basic": 0, "business": 0, "growth": 0, "pro": 0}
    for item in all_items:
        plan = str((item or {}).get("plan") or "basic").lower()
        if plan in plan_counts:
            plan_counts[plan] += 1
    stripe_safe_for_pilot = (STRIPE_MODE == "disabled") or (
        STRIPE_MODE == "test" and bool(STRIPE_SECRET_KEY) and bool(STRIPE_WEBHOOK_SECRET)
    )
    email_safe_for_pilot = (not bool(email_cfg.get("delivery_enabled"))) or bool(email_cfg.get("ready_for_real_delivery"))
    checks = [
        {"id": "runtime_not_production", "label": "Closed pilot is not running as public production", "ready": runtime_config.env in {"development", "staging"}, "kind": "deployment", "env": runtime_config.env},
        {"id": "persistent_data", "label": "Database/uploads/backups are outside replaceable code", "ready": bool(runtime_config.user_data_outside_code_dir), "kind": "storage", "details": _persistent_data_snapshot()},
        {"id": "uploads_writable", "label": "Uploads directory is writable", "ready": _directory_writable(runtime_config.uploads_dir), "kind": "storage"},
        {"id": "backup_writable", "label": "Backup directory is writable", "ready": _directory_writable(runtime_config.backup_dir), "kind": "backup"},
        {"id": "admin_session", "label": "Admin session login is available", "ready": True, "kind": "security"},
        {"id": "demo_seed_safe", "label": "Demo seeding is safe for the selected environment", "ready": (not is_production()) and (is_development() or not runtime_config.enable_demo_seed), "kind": "security", "enabled": bool(runtime_config.enable_demo_seed)},
        {"id": "public_base_url", "label": "Public/staging base URL is set when not local", "ready": is_development() or bool(runtime_config.public_base_url.startswith("https://")), "kind": "deployment", "url_set": bool(runtime_config.public_base_url)},
        {"id": "stripe_pilot_safe", "label": "Stripe is test-configured or explicitly disabled", "ready": stripe_safe_for_pilot, "kind": "stripe", "mode": STRIPE_MODE},
        {"id": "email_pilot_safe", "label": "Email is safe for pilot: manual mode or configured provider", "ready": email_safe_for_pilot, "kind": "email", "provider": email_cfg.get("provider"), "delivery_enabled": email_cfg.get("delivery_enabled")},
        {"id": "published_listing_available", "label": "At least one published kitchen is visible on Explore", "ready": len(public_items) >= 1, "kind": "content", "public_count": len(public_items)},
    ]
    ready_count = sum(1 for c in checks if c.get("ready"))
    return {
        "checks": checks,
        "ready_count": ready_count,
        "total_count": len(checks),
        "pilot_ready": ready_count == len(checks),
        "mode": "pilot-ready" if ready_count == len(checks) else "pilot-not-ready",
        "listings": {"total": len(all_items), "public": len(public_items), "plan_counts": plan_counts},
        "stripe": {"mode": STRIPE_MODE, "safe_for_pilot": stripe_safe_for_pilot, "all_supported_currency_prices_ready": stripe_cfg.get("all_supported_currency_prices_ready")},
        "email": {"provider": email_cfg.get("provider"), "delivery_enabled": email_cfg.get("delivery_enabled"), "ready_for_real_delivery": email_cfg.get("ready_for_real_delivery")},
    }



def _prelaunch_readiness_snapshot() -> dict:
    """Final pre-launch checklist for moving from pilot/staging toward live use.

    This is stricter than pilot readiness, but it does not require adding new
    app features. It verifies the operating conditions that protect user data,
    admin access, Stripe, email and deploy stability.
    """
    email_cfg = _email_config_snapshot(get_admin_settings())
    stripe_cfg = _stripe_config_snapshot()
    try:
        users = list_app_users()
    except Exception:
        users = []
    admin_count = len([u for u in users if str((u or {}).get("role") or "") == "admin" and bool((u or {}).get("active", True))])
    try:
        public_items = db_list_listings(include_drafts=False)
    except Exception:
        public_items = []
    stripe_live_or_disabled = (STRIPE_MODE == "disabled") or (
        STRIPE_MODE == "live" and bool(STRIPE_SECRET_KEY) and bool(STRIPE_WEBHOOK_SECRET)
    )
    stripe_test_ok_for_staging = runtime_config.env == "staging" and STRIPE_MODE == "test" and bool(STRIPE_SECRET_KEY) and bool(STRIPE_WEBHOOK_SECRET)
    stripe_ready = bool(stripe_live_or_disabled or stripe_test_ok_for_staging)
    checks = [
        {"id":"env_not_development", "label":"Environment is staging or production", "ready":runtime_config.env in {"staging", "production"}, "kind":"deployment", "env":runtime_config.env},
        {"id":"persistent_user_data", "label":"Database, uploads and backups are outside replaceable code", "ready":bool(runtime_config.user_data_outside_code_dir), "kind":"storage", "details":_persistent_data_snapshot()},
        {"id":"uploads_writable", "label":"Uploads directory is writable", "ready":_directory_writable(runtime_config.uploads_dir), "kind":"storage"},
        {"id":"backup_writable", "label":"Backup directory is writable", "ready":_directory_writable(runtime_config.backup_dir), "kind":"backup"},
        {"id":"backup_configured", "label":"Backup is configured/acknowledged", "ready":bool(runtime_config.backup_configured), "kind":"backup", "details":_backup_config_snapshot()},
        {"id":"public_https_url", "label":"Public base URL is HTTPS", "ready":bool(runtime_config.public_base_url and runtime_config.public_base_url.startswith("https://")), "kind":"security", "url_set":bool(runtime_config.public_base_url)},
        {"id":"session_secret", "label":"Long session secret is configured", "ready":bool(runtime_config.session_secret and len(runtime_config.session_secret) >= 32), "kind":"security"},
        {"id":"legacy_admin_disabled", "label":"Legacy admin-key fallback is disabled", "ready":not bool(runtime_config.legacy_admin_key_available), "kind":"security"},
        {"id":"admin_user_exists", "label":"At least one active admin user exists", "ready":admin_count >= 1, "kind":"security", "admin_count":admin_count},
        {"id":"demo_seed_disabled", "label":"Demo seeding is disabled for web launch", "ready":not bool(runtime_config.enable_demo_seed or runtime_config.allow_demo_seed), "kind":"security"},
        {"id":"stripe_ready", "label":"Stripe is live-ready, staging-test-ready or explicitly disabled", "ready":stripe_ready, "kind":"stripe", "mode":STRIPE_MODE, "all_supported_currency_prices_ready":stripe_cfg.get("all_supported_currency_prices_ready")},
        {"id":"email_ready", "label":"Email delivery is configured or intentionally manual", "ready":bool(email_cfg.get("ready_for_real_delivery")) or not bool(email_cfg.get("delivery_enabled")), "kind":"email", "provider":email_cfg.get("provider"), "delivery_enabled":email_cfg.get("delivery_enabled")},
        {"id":"error_logging", "label":"Error logging is configured", "ready":bool(runtime_config.error_log_configured), "kind":"monitoring"},
        {"id":"error_monitoring", "label":"Error monitoring is configured/acknowledged", "ready":bool(runtime_config.error_monitoring_configured), "kind":"monitoring"},
        {"id":"visible_listing", "label":"At least one kitchen is visible on Explore", "ready":len(public_items) >= 1, "kind":"content", "public_count":len(public_items)},
    ]
    ready_count = sum(1 for c in checks if c.get("ready"))
    return {
        "checks": checks,
        "ready_count": ready_count,
        "total_count": len(checks),
        "prelaunch_ready": ready_count == len(checks),
        "mode": "prelaunch-ready" if ready_count == len(checks) else "prelaunch-not-ready",
        "environment": runtime_config.env,
        "stripe": {"mode": STRIPE_MODE, "ready": stripe_ready, "all_supported_currency_prices_ready": stripe_cfg.get("all_supported_currency_prices_ready")},
        "email": {"provider": email_cfg.get("provider"), "delivery_enabled": email_cfg.get("delivery_enabled"), "ready_for_real_delivery": email_cfg.get("ready_for_real_delivery")},
        "listings": {"public": len(public_items)},
        "admins": {"active_admin_count": admin_count},
    }


def _safe_dir_size_and_count(path: str, max_files: int = 5000) -> dict:
    """Return a small safe summary of a directory without exposing file names."""
    p = Path(path) if path else None
    if not p or not p.exists() or not p.is_dir():
        return {"exists": False, "file_count": 0, "size_bytes": 0, "truncated": False}
    total = 0
    count = 0
    truncated = False
    try:
        for item in p.rglob("*"):
            if item.is_file():
                count += 1
                try:
                    total += item.stat().st_size
                except Exception:
                    pass
                if count >= max_files:
                    truncated = True
                    break
    except Exception:
        truncated = True
    return {"exists": True, "file_count": count, "size_bytes": total, "truncated": truncated}



def _directory_writable(path_value: str) -> bool:
    if not path_value:
        return False
    try:
        path = Path(path_value)
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".ricemap24-write-test"
        test_file.write_text("ok", encoding="utf-8")
        try:
            test_file.unlink()
        except Exception:
            pass
        return True
    except Exception:
        return False

def _backup_config_snapshot() -> dict:
    db_path = runtime_config.database_path if runtime_config.database_engine == "sqlite" else ""
    db_exists = bool(db_path and Path(db_path).exists())
    db_size = 0
    if db_exists:
        try:
            db_size = Path(db_path).stat().st_size
        except Exception:
            db_size = 0
    backup_dir = Path(runtime_config.backup_dir) if runtime_config.backup_dir else None
    backup_dir_exists = bool(backup_dir and backup_dir.exists() and backup_dir.is_dir())
    return {
        "configured": bool(runtime_config.backup_configured),
        "backup_dir_set": bool(runtime_config.backup_dir),
        "backup_dir_exists": backup_dir_exists,
        "backup_uploads_enabled": bool(runtime_config.backup_uploads_enabled),
        "database_engine": runtime_config.database_engine,
        "sqlite_database_exists": db_exists,
        "sqlite_database_size_bytes": db_size,
        "uploads": _safe_dir_size_and_count(runtime_config.uploads_dir),
        "local_backup_supported": runtime_config.database_engine == "sqlite",
    }


def _run_local_backup() -> dict:
    """Create a local zip backup for SQLite + uploads. Intended for dev/staging/persistent-disk deployments."""
    if runtime_config.database_engine != "sqlite":
        raise HTTPException(status_code=400, detail="Local backup is only supported for SQLite in this build.")
    db_path = Path(runtime_config.database_path) if runtime_config.database_path else None
    if not db_path or not db_path.exists():
        raise HTTPException(status_code=400, detail="SQLite database file was not found.")
    backup_dir = Path(runtime_config.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"ricemap24-backup-{runtime_config.env}-{stamp}.zip"
    uploads_path = Path(runtime_config.uploads_dir) if runtime_config.uploads_dir else None
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, arcname="ricemap24.sqlite3")
        manifest = {
            "created_at_utc": datetime.utcnow().isoformat() + "Z",
            "environment": runtime_config.env,
            "release_version": runtime_config.release_version,
            "database_engine": runtime_config.database_engine,
            "uploads_included": False,
        }
        if runtime_config.backup_uploads_enabled and uploads_path and uploads_path.exists() and uploads_path.is_dir():
            manifest["uploads_included"] = True
            for item in uploads_path.rglob("*"):
                if item.is_file():
                    try:
                        zf.write(item, arcname=str(Path("uploads") / item.relative_to(uploads_path)))
                    except Exception:
                        pass
        zf.writestr("backup-manifest.json", json.dumps(manifest, indent=2))
    try:
        size = target.stat().st_size
    except Exception:
        size = 0
    return {"ok": True, "filename": target.name, "size_bytes": size, "backup_dir_exists": True}

# SMTP (for sending receipts/invoices)
SMTP_HOST = os.environ.get("RICEMAP_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("RICEMAP_SMTP_PORT", "587") or 587)
SMTP_USER = os.environ.get("RICEMAP_SMTP_USER", "")
SMTP_PASS = os.environ.get("RICEMAP_SMTP_PASS", "")
SMTP_FROM = os.environ.get("RICEMAP_SMTP_FROM", "")
SMTP_FROM_NAME = os.environ.get("RICEMAP_SMTP_FROM_NAME", "")
SMTP_TLS = (os.environ.get("RICEMAP_SMTP_TLS", "1") != "0")


def _smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_FROM)


def _send_email_with_pdf(to_email: str, subject: str, body: str, pdf_bytes: bytes, filename: str) -> None:
    """Send a receipt/invoice PDF through the same email provider as admin mail.

    Earlier builds only used the legacy RICEMAP_SMTP_* variables here. For
    staging/production this must use the real configured provider
    (Postmark/SMTP/SendGrid) so receipt emails do not silently depend on a
    separate legacy setup.
    """
    _send_transactional_email(
        to_email=to_email,
        subject=subject or "Receipt",
        body=body or "",
        attachments=[{
            "content": pdf_bytes,
            "filename": filename or "receipt.pdf",
            "maintype": "application",
            "subtype": "pdf",
        }],
    )



    return bool(SMTP_HOST and SMTP_FROM)




@app.get("/r/amazon")
async def r_amazon(request: Request, country: str = "NO", t: str = "", region: str = "", page: str = "supplies"):
    """Landing page for Amazon links (small orders).

    Shows a short disclosure and category buttons. Each click logs to /api/supplier-click
    using the kitchen preview token, then redirects to Amazon with the correct storefront/tag.

    Note: This is intentionally simple MVP (no server-side HTML templates).
    """
    country = (country or "NO").upper().strip()
    storefront = "se"
    if country in ("DK",):
        storefront = "de"
    elif country in ("SE","NO"):
        storefront = "se"
    # Associate tags are per storefront. Override via env vars.
    tag_se = os.getenv("AMAZON_TAG_SE", "ricemap24se-21")
    tag_de = os.getenv("AMAZON_TAG_DE", "ricemap24de-21")
    tag = tag_de if storefront == "de" else tag_se

    # Force English UI on Amazon by using the explicit locale path.
    # This avoids depending on cookies / browser language.
    base = f"https://www.amazon.{storefront}/-/en/s"
    # Pre-made search terms (user can still use Amazon filters).
    # Keep these generic so they work across locales.
    # Shortcut buttons (keep these broad so they work across locales).
    # Note: Amazon inventory varies per country; these are search-based.
    items = [
        ("takeaway", "Takeaway containers", "takeaway containers leakproof"),
        ("sauce", "Sauce cups + lids", "sauce cups with lids"),
        ("bags", "Paper bags", "kraft paper bags with handles"),
        ("labels", "Stickers / labels", "logo stickers small business"),

        ("straws", "Straws (paper / smoothie)", "paper straws for drinks"),

        # New: drinks + temperature control
        ("hotcups", "Hot drink cups + lids", "paper coffee cups with lids 12 oz"),
        ("coldcups", "Cold drink cups (smoothie) + lids", "plastic cups with dome lids 16 oz"),

        # Temperature / delivery helpers
        ("insulated_bag", "Insulated delivery bags", "insulated delivery bag thermal"),
        ("foil_pouch", "Thermal foil pouches (small)", "thermal foil bag for food"),
        # Use 'foodpack aluminium' wording to avoid body/medical results.
        ("heatpacks", "Heat food packs (aluminium)", "heat foodpack aluminium"),
        # Avoid medical/body results by being explicit about coolers/food delivery.
        ("icepacks", "Gel ice packs (for bags)", "gel ice packs for cooler reusable"),
    ]
    title = "Amazon (small orders)"
    disclosure = "Affiliate partner: RiceMap24 may earn from qualifying purchases."
    # Keep this page English-first (user requested). If you later want i18n,
    # add a lang switch here again.
    disclosure_text = disclosure

    # Build HTML (tiny, dependency-free)
    # IMPORTANT: Do NOT use an f-string here because the inline JS contains many
    # curly braces which can break f-string parsing. Use Template instead.
    tpl = Template("""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>$title</title>
  <style>
    :root{
      --bg:#F7F0E5;
      --panel:#FFFFFF;
      --text:#241F1A;
      --muted:#74685C;
      --border:#E2D6C7;
      --accent:#103D25;
      --accent-dark:#0B2F1C;
      --accent-soft:#E7F1E5;
      --soft:#EEF6EA;
      --gold:#D9A441;
      --shadow:0 18px 38px rgba(36,28,23,.09);
    }
    *{box-sizing:border-box;}
    body{
      font-family:Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      margin:0;
      background:
        radial-gradient(circle at top left, rgba(111,163,67,.20), transparent 32%),
        linear-gradient(180deg, #fbf7ef 0%, var(--bg) 48%, #f4eadc 100%);
      color:var(--text);
    }
    .topbar{
      background:rgba(255,255,255,.92);
      border-bottom:1px solid var(--border);
      backdrop-filter:saturate(180%) blur(10px);
    }
    .topbar-inner{
      max-width: 960px;
      margin:0 auto;
      padding:13px 18px;
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:12px;
    }
    .brand{
      display:flex;
      align-items:center;
      gap:10px;
      font-weight:900;
      letter-spacing:-.035em;
      color:var(--accent);
      font-size:21px;
      line-height:1;
    }
    .brand .mark{
      width:42px;
      height:42px;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      flex:0 0 auto;
    }
    .brand .mark svg{
      width:42px;
      height:42px;
      display:block;
    }
    .brand .rm24{color:#6FA343;}
    .back{
      color:var(--accent-dark);
      border:1px solid rgba(16,61,37,.24);
      background:#fff;
      padding:9px 13px;
      border-radius:999px;
      font-size:13px;
      font-weight:750;
      text-decoration:none;
      box-shadow:0 8px 18px rgba(11,47,28,.07);
      white-space:nowrap;
    }
    .wrap{max-width: 960px; margin: 0 auto; padding: 26px 18px 44px;}
    .hero{
      display:grid;
      grid-template-columns: 1fr;
      gap:14px;
      margin-bottom:14px;
    }
    @media (min-width:760px){.hero{grid-template-columns:1.15fr .85fr; align-items:stretch;}}
    .card{
      background:rgba(255,255,255,.94);
      border:1px solid var(--border);
      border-radius:24px;
      padding:22px;
      box-shadow:var(--shadow);
    }
    .green-card{
      background:linear-gradient(135deg, var(--accent-dark), var(--accent));
      color:#fff;
      border-color:rgba(255,255,255,.12);
      overflow:hidden;
      position:relative;
    }
    .green-card:after{
      content:'';
      position:absolute;
      right:-70px;
      top:-70px;
      width:190px;
      height:190px;
      border-radius:999px;
      background:rgba(139,191,86,.20);
    }
    h1{font-size:clamp(28px,4vw,46px); line-height:1.02; margin:0 0 10px; letter-spacing:-.045em;}
    h2{font-size:17px; margin:24px 0 8px; color:var(--accent-dark); letter-spacing:-.02em;}
    p{margin:8px 0; color:var(--muted); line-height:1.55;}
    .green-card p{color:rgba(255,255,255,.84); max-width:58ch;}
    p.tip{font-size:15px; font-weight:750; color:#fff;}
    .grid{display:grid; grid-template-columns:1fr; gap:12px; margin-top:14px;}
    @media (min-width:700px){.grid{grid-template-columns:1fr 1fr;}}
    a.btn{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:12px;
      min-height:54px;
      text-decoration:none;
      color:var(--accent-dark);
      background:#fff;
      padding:14px 16px;
      border-radius:16px;
      font-weight:800;
      border:1px solid rgba(16,61,37,.16);
      box-shadow:0 10px 22px rgba(11,47,28,.07);
    }
    a.btn:after{content:'→'; color:#6FA343; font-weight:900;}
    a.btn:hover{border-color:rgba(16,61,37,.34); box-shadow:0 14px 28px rgba(11,47,28,.12); transform:translateY(-1px);}
    .select{
      width:100%;
      margin-top:10px;
      background:#fff;
      color:var(--text);
      border:1px solid var(--border);
      border-radius:16px;
      padding:13px 14px;
      font-weight:700;
      box-shadow:0 8px 18px rgba(11,47,28,.05);
    }
    .muted{font-size:13px; color:var(--muted); margin-top:10px;}
    .disclosure{font-size:12px; color:var(--muted); margin-top:18px; border-top:1px solid var(--border); padding-top:12px;}
    .top{display:flex; align-items:flex-start; justify-content:space-between; gap:12px; position:relative; z-index:1;}
    .pill{font-size:12px; padding:7px 11px; border-radius:999px; background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.18); color:#fff; white-space:nowrap;}
    .small-pill{display:inline-flex; margin-top:6px; font-size:12px; padding:7px 10px; border-radius:999px; background:var(--accent-soft); color:var(--accent-dark); font-weight:800;}
    .section-card{margin-top:14px;}
  </style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-inner">
      <div class="brand"><span class="mark"><svg viewBox="0 0 64 64" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg"><path d="M12.5 33.5c1.8 10.8 9.8 18 19.5 18s17.7-7.2 19.5-18H12.5Z" fill="#103D25"/><path d="M18.5 30.5c3.7-7.4 22.6-7.4 27.1 0" fill="none" stroke="#103D25" stroke-width="5" stroke-linecap="round"/><path d="M18.2 34.5c4.7 2.5 23.7 2.5 28.2 0" fill="none" stroke="#0B2F1C" stroke-width="2" stroke-linecap="round" opacity=".24"/><circle cx="24" cy="40" r="4.7" fill="#FFFDF7" opacity=".95"/><ellipse cx="37.5" cy="43" rx="7.1" ry="5.1" fill="#FFFDF7" opacity=".95"/><path d="M40.5 19.5 55 12.2" stroke="#103D25" stroke-width="4" stroke-linecap="round"/><path d="M43.5 25 58 17.7" stroke="#103D25" stroke-width="4" stroke-linecap="round"/><path d="M22.5 18c-2.4-3.2.3-5.6 4.5-5.6" fill="none" stroke="#103D25" stroke-width="3" stroke-linecap="round" opacity=".9"/></svg></span><span>RiceMap<span class="rm24">24</span></span></div>
      <a class="back" href="/">Back to RiceMap24</a>
    </div>
  </div>
  <div class="wrap">
    <div class="hero">
      <div class="card green-card">
        <div class="top">
          <div>
            <h1>$title</h1>
            <p class="tip">Small-order packaging shortcuts for home kitchens.</p>
          </div>
          <div class="pill">amazon.$storefront • $country</div>
        </div>
        <p>Amazon is often useful for testing, low quantities and quick replacement orders. For larger volume, local suppliers may be better.</p>
      </div>
      <div class="card">
        <span class="small-pill">Supplier shortcuts</span>
        <h2 style="margin-top:12px">Before you order</h2>
        <p>These buttons open Amazon searches, not fixed products. Check size, quantity, delivery date and price before buying.</p>
      </div>
    </div>
    <div class="card section-card">
      <h2 style="margin-top:0">Popular packaging searches</h2>
      <div class="grid" id="grid"></div>
    </div>
    <div class="card section-card">
      <h2 style="margin-top:0">Packaging by dish type</h2>
      <p class="muted">Choose a dish type to see 5 packaging options. We use searches instead of single products so you can pick the best price and size.</p>
      <select id="dishSelect" class="select"></select>
      <div class="grid" id="dishGrid"></div>
      <p class="muted">You can safely close this page after Amazon opens.</p>
      <p class="disclosure">$disclosure_text</p>
    </div>
  </div>

<script>
(function() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('t') || '';
  const region = params.get('region') || '$country';
  const page = params.get('page') || '$page';
  const dishParam = (params.get('dish') || '').toLowerCase();
  const lang = params.get('lang') || '';
  const base = $base_json;
  const tag = $tag_json;
  const items = $items_json;
  const grid = document.getElementById('grid');
  const dishSelect = document.getElementById('dishSelect');
  const dishGrid = document.getElementById('dishGrid');

  // Dish → packaging searches (5 options each). Search-based so links don't go stale.
  const DISH_PACKAGING = {
    "Baguettes / sandwiches": [
      ["bag_greaseproof", "Greaseproof baguette bags", "take away baguette bag greaseproof"],
      ["bag_window", "Baguette bags with window", "baguette bag with window"],
      ["bag_kraft", "Kraft baguette bags", "kraft baguette bag"],
      ["bag_long", "Long sandwich paper bags", "long sandwich paper bag"],
      ["bag_sleeves", "Baguette paper sleeves", "baguette paper sleeve"]
    ],
    "Soups / pho / ramen": [
      ["soup_cups", "Soup cups + lids", "soup cups with lids kraft"],
      ["ramen_bowls", "Ramen bowls + lids", "ramen bowls with lids"],
      ["leakproof", "Leakproof containers", "leakproof takeaway containers"],
      ["insulated", "Thermal foil pouches", "thermal foil bag for food"],
      ["labels", "Tamper/labels", "tamper evident stickers food"]
    ],
    "Rice bowls / curries": [
      ["pp_cont", "Microwaveable containers", "microwaveable meal prep containers with lids"],
      ["portion", "Portion containers", "portion cups with lids food"],
      ["carry", "Carry bags", "kraft paper bags with handles"],
      ["heat", "Heat food packs (aluminium)", "heat foodpack aluminium"],
      ["stickers", "Stickers / labels", "logo stickers small business"]
    ],
    "Desserts / pastry": [
      ["clamshell", "Dessert clamshell boxes", "dessert clamshell container"],
      ["cake_box", "Cake / pastry boxes", "pastry boxes with window"],
      ["paper_bags", "Paper pastry bags", "paper pastry bags"],
      ["cold_cups", "Cold cups (for mousse)", "plastic cups with dome lids 12 oz"],
      ["labels2", "Stickers / labels", "logo stickers small business"]
    ],
    "Drinks (hot / cold)": [
      ["hotcups", "Hot drink cups + lids", "paper coffee cups with lids 12 oz"],
      ["coldcups", "Cold drink cups + lids", "plastic cups with dome lids 16 oz"],
      ["straws", "Straws (paper / smoothie)", "straw paper smoothie"],
      ["icepacks", "Gel ice packs (for bags)", "gel ice packs for cooler reusable"],
      ["stickers3", "Stickers / labels", "logo stickers small business"]
    ]
  };

  function renderDishOptions() {
    if (!dishSelect || !dishGrid) return;
    dishSelect.innerHTML = "";
    const keys = Object.keys(DISH_PACKAGING);
    const DISH_PARAM_TO_KEY = {
      'baguette': 'Baguettes / sandwiches',
      'baguettes': 'Baguettes / sandwiches',
      'sandwich': 'Baguettes / sandwiches',
      'sandwiches': 'Baguettes / sandwiches',
      'wrap': 'Baguettes / sandwiches',
      'wraps': 'Baguettes / sandwiches',
      'soups': 'Soups / pho / ramen',
      'soup': 'Soups / pho / ramen',
      'pho': 'Soups / pho / ramen',
      'ramen': 'Soups / pho / ramen',
      'rice': 'Rice bowls / curries',
      'bowl': 'Rice bowls / curries',
      'bowls': 'Rice bowls / curries',
      'curry': 'Rice bowls / curries',
      'curries': 'Rice bowls / curries',
      'dessert': 'Desserts / pastry',
      'desserts': 'Desserts / pastry',
      'pastry': 'Desserts / pastry',
      'cake': 'Desserts / pastry',
      'drinks': 'Drinks (hot / cold)',
      'drink': 'Drinks (hot / cold)',
      'coffee': 'Drinks (hot / cold)',
      'tea': 'Drinks (hot / cold)',
      'smoothie': 'Drinks (hot / cold)',
      'lemonade': 'Drinks (hot / cold)'
    };
    const preferredKey = DISH_PARAM_TO_KEY[dishParam] || '';

    keys.forEach((k, idx) => {
      const opt = document.createElement('option');
      opt.value = k;
      opt.textContent = k;
      if ((preferredKey && k === preferredKey) || (!preferredKey && idx === 0)) opt.selected = true;
      dishSelect.appendChild(opt);
    });

    function draw() {
      dishGrid.innerHTML = "";
      const key = dishSelect.value;
      const rows = DISH_PACKAGING[key] || [];
      rows.forEach(([id, name, q]) => {
        const a = document.createElement('a');
        a.href = '#';
        a.className = 'btn';
        a.textContent = name;
        a.addEventListener('click', (e) => {
          e.preventDefault();
          trackAndGo('dish_' + id, key + ' — ' + name, q);
        });
        dishGrid.appendChild(a);
      });
    }

    dishSelect.addEventListener('change', draw);
    draw();
  }


  function trackAndGo(itemId, itemName, q) {
    const url = base + '?k=' + encodeURIComponent(q) + (tag ? ('&tag=' + encodeURIComponent(tag)) : '');
    // best-effort tracking (never blocks redirect)
    try {
      if (token) {
        const payload = {
          token,
          region,
          lang,
          page,
          supplier: {
            id: 'amazon_' + region.toLowerCase() + '_' + itemId,
            name: 'Amazon (' + region + ') — ' + itemName,
            url,
            region
          }
        };
        const body = JSON.stringify(payload);
        if (navigator.sendBeacon) {
          const blob = new Blob([body], { type: 'application/json' });
          navigator.sendBeacon('/api/supplier-click', blob);
        } else {
          fetch('/api/supplier-click', { method:'POST', headers:{'Content-Type':'application/json'}, body, keepalive:true }).catch(()=>{});
        }
      }
    } catch(e) {}
    window.location.href = url;
  }

  items.forEach(([id, name, q]) => {
    const a = document.createElement('a');
    a.href = '#';
    a.className = 'btn';
    a.textContent = name;
    a.addEventListener('click', (e) => {
      e.preventDefault();
      trackAndGo(id, name, q);
    });
    grid.appendChild(a);
  });
  renderDishOptions();
})();
</script>
</body>
</html>""")

    html = tpl.safe_substitute(
        title=title,
        storefront=storefront,
        country=country,
        page=page,
        disclosure_text=disclosure_text,
        base_json=json.dumps(base),
        tag_json=json.dumps(tag),
        items_json=json.dumps(items),
    )
    return Response(content=html, media_type="text/html")
@app.on_event("startup")
def _startup():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    # Safe demo/test seed: allowed explicitly in local/dev, and also in staging
    # when the PostgreSQL database is empty so staging does not show a broken/empty marketplace.
    # Production never auto-seeds demo data.
    if runtime_config.allow_demo_seed:
        demo_listings = []
        for item in LISTINGS:
            demo_item = dict(item)
            demo_item["is_demo"] = True
            demo_item["listing_type"] = "demo"
            demo_item["accepts_orders"] = False
            demo_item["show_in_actor_marketing"] = True
            demo_item["show_in_customer_marketplace"] = True
            # Demo/test listings must remain visible with billing guards enabled.
            demo_item["access_type"] = "internal"
            demo_item["paid_status"] = "paid"
            demo_item["account_status"] = "active"
            demo_item["plan_active"] = 1
            demo_listings.append(demo_item)
        seed_if_empty(demo_listings)
        # Demo convenience: plan mix for local/staging testing only.
        ensure_plan("marias-filipino-kusina", "pro")
        ensure_plan("linh-viet-kitchen", "basic")
        ensure_plan("noks-thai-corner", "business")


@app.get("/health")
def health():
    email_snapshot = _email_config_snapshot()
    pilot_snapshot = _pilot_readiness_snapshot()
    prelaunch_snapshot = _prelaunch_readiness_snapshot()
    return {
        "ok": True,
        "version": app.version,
        "env": runtime_config.env,
        "database_engine": runtime_config.database_engine,
        "database_url_set": bool(runtime_config.database_url),
        "persistent_data_dir_set": bool(runtime_config.persistent_data_dir_set),
        "database_inside_code_dir": bool(runtime_config.database_inside_code_dir),
        "uploads_inside_code_dir": bool(runtime_config.uploads_inside_code_dir),
        "backup_inside_code_dir": bool(runtime_config.backup_inside_code_dir),
        "user_data_outside_code_dir": bool(runtime_config.user_data_outside_code_dir),
        "auth_sessions_ready": True,
        "session_days": runtime_config.session_days,
        "login_lockout_minutes": runtime_config.login_lockout_minutes,
        "upload_storage_mode": runtime_config.upload_storage_mode,
        "uploads_dir_set": bool(runtime_config.uploads_dir),
        "uploads_dir_writable": _directory_writable(runtime_config.uploads_dir),
        "backup_dir_writable": _directory_writable(runtime_config.backup_dir),
        "upload_max_mb": runtime_config.upload_max_mb,
        "stripe_mode": STRIPE_MODE,
        "stripe_secret_key_set": bool(STRIPE_SECRET_KEY),
        "stripe_webhook_secret_set": bool(STRIPE_WEBHOOK_SECRET),
        "email_provider": email_snapshot.get("provider"),
        "email_delivery_enabled": email_snapshot.get("delivery_enabled"),
        "email_ready_for_real_delivery": email_snapshot.get("ready_for_real_delivery"),
        "deployment_provider": runtime_config.deployment_provider,
        "deployment_region_set": bool(runtime_config.deployment_region),
        "public_base_url_set": bool(runtime_config.public_base_url),
        "release_version": runtime_config.release_version,
        "pilot_ready": bool(pilot_snapshot.get("pilot_ready")),
        "pilot_ready_count": pilot_snapshot.get("ready_count"),
        "pilot_total_count": pilot_snapshot.get("total_count"),
        "demo_seed_enabled": bool(runtime_config.enable_demo_seed),
        "demo_seed_allowed": bool(runtime_config.allow_demo_seed),
        "legacy_admin_key_available": bool(runtime_config.legacy_admin_key_available),
        "git_commit_set": bool(runtime_config.git_commit_sha),
        "port": runtime_config.port,
        "backup_configured": bool(runtime_config.backup_configured),
        "backup_dir_set": bool(runtime_config.backup_dir),
        "backup_uploads_enabled": bool(runtime_config.backup_uploads_enabled),
        "error_monitoring_configured": bool(runtime_config.error_monitoring_configured),
        "error_log_configured": bool(runtime_config.error_log_configured),
        "request_logging_enabled": bool(runtime_config.request_logging_enabled),
        "log_level": runtime_config.log_level,
    }



# --- Premium assets: QR + Poster (owner tools) ---------------------------------

def _public_listing_url(request: Request, slug: str) -> str:
    origin = _origin_from_request(request)
    return origin.rstrip("/") + "/c/" + slug


PLAN_LEVEL = {"basic": 0, "business": 1, "growth": 2, "pro": 3, "standard": 1, "plus": 2, "premium": 1}
# Access model: Business has full Business Coach; Growth/Pro add Pro Print Kit and strategy layers; Pro adds BriteSight Creative Suite.


def _normalize_plan(p: str) -> str:
    p = (p or "basic").lower().strip()
    if p in ("premium", "standard"):
        return "business"
    if p == "plus":
        return "growth"
    if p not in ("basic", "business", "growth", "pro"):
        return "basic"
    return p




def _feature_override_active(listing: dict, key: str) -> bool:
    raw = (listing or {}).get("feature_overrides") or {}
    if isinstance(raw, list):
        raw = {str(k): {"enabled": True, "start": "", "end": ""} for k in raw if k}
    if not isinstance(raw, dict):
        return False
    cfg = raw.get(key) or {}
    if not isinstance(cfg, dict):
        cfg = {"enabled": bool(cfg)}
    if cfg.get("enabled") is False:
        return False
    today = datetime.utcnow().date().isoformat()
    start = str(cfg.get("start") or cfg.get("start_date") or "")[:10]
    end = str(cfg.get("end") or cfg.get("end_date") or "")[:10]
    if start and today < start:
        return False
    if end and today > end:
        return False
    return True

def _require_plan(listing: dict, min_plan: str = "standard") -> None:
    cur = _normalize_plan(str(listing.get("plan") or "basic"))
    need = _normalize_plan(min_plan)
    if PLAN_LEVEL.get(cur, 0) < PLAN_LEVEL.get(need, 0):
        raise HTTPException(status_code=403, detail=f"{need.capitalize()} required")
    # Allow downloads even if pending activation (owner preparing print).
    # If you want to hard-require active subscription, change this to ==1.
    # if int(listing.get("plan_active", 0)) != 1:
    #     raise HTTPException(status_code=403, detail="Active subscription required")




# --- Recipes: indexing, paywalls, and lightweight markdown->HTML ------------

_RECIPES_INDEX: dict[str, dict] = {}
_RECIPES_ORDER: list[str] = []
_TRIAL_IDS: set[str] = set()
_STANDARD_STRATEGY_IDS: set[str] = set()


def _stable_int(s: str) -> int:
    import hashlib
    return int(hashlib.sha1(s.encode('utf-8')).hexdigest()[:8], 16)


def _infer_tags(recipe_id: str, title: str) -> dict:
    """Infer lightweight tags from filename + title.

    Important: This must *not* feel random.
    We use deterministic heuristics and prioritize explicit markers found in the
    recipe_id (filename stem) such as "sideorder" and "baguette".
    """
    import re

    s = (recipe_id + " " + (title or "")).lower()

    # --- cuisine -----------------------------------------------------------
    cuisines: list[str] = []
    for k in [
        "thai","vietnam","viet","filipino","philipp","korean","japanese","indian","myanmar","burmese",
        "chinese","hong-kong","malay","indones","singapore","sri-lanka","nepal",
    ]:
        if k in s:
            cuisines.append("vietnamese" if k in ("viet","vietnam") else ("filipino" if k.startswith("philipp") else k))
    if not cuisines:
        cuisines = ["asian"]

    # --- role/type ---------------------------------------------------------
    # Prefer explicit markers in filename.
    rid = recipe_id.lower()

    def has_word(w: str) -> bool:
        return re.search(rf"\b{re.escape(w)}\b", s) is not None

    role = "main_light"  # default
    rtype = "main"
    forced_role = False

    # Drinks and desserts must be explicit (avoid misclassifying "sweet chili", "rice cakes", etc.)
    # We prefer conservative classification: if uncertain, keep as main/side (not dessert/drink).
    dessert_kw = [
        "dessert","mochi","pudding","ice cream","gelato","brownie","cookie",
        "mango sticky","tiramisu"
    ]
    # Treat "cake" as dessert ONLY when it's clearly a sweet cake (not "rice cakes"/tteok).
    dessert_cake_kw = ["cake","cupcake","cheesecake","sponge cake"]
    dessert_sweet_markers = [
        "nutella","chocolate","cocoa","vanilla","caramel","honey","maple","syrup",
        "berry","strawberry","blueberry","banana","sweet"
    ]

    drink_kw = [
        "drink","iced tea","thai tea","coffee","latte","cappuccino","juice","lemonade",
        "smoothie","shake","boba","soda","sparkling"
    ]

    # --- explicit savory overrides (common misclassifications) -------------
    # "custard" appears in savory dishes like Hor Mok (Thai fish curry custard) -> NOT dessert.
    savory_custard_markers = ["hor mok","pla","fish curry","steamed fish","thai steamed","curry custard"]
    # Rice cakes in Korean/Asian context are savory (tteokbokki) -> NOT dessert.
    savory_ricecake_markers = ["tteokbokki","tteok","rice cake","rice cakes","korean rice cake"]

    # Hor Mok Pla is a savory Thai steamed fish curry custard; keep it under mains.
    if any(m in s for m in ["hor mok", "hor-mok", "thai steamed fish curry custard"]):
        role, rtype = "main_light", "main"
        forced_role = True

    # Korean rice cakes / tteokbokki are savory side orders.
    if not forced_role and any(m in s for m in ["tteokbokki"]):
        role, rtype = "side", "side"
        forced_role = True

    # Savory pancakes/jeon are usually side orders (not dessert, not handheld).
    if not forced_role and ("pancake" in s or "pajeon" in s or "jeon" in s or "banh khot" in s or "okonomiyaki" in s):
        sweet_pancake_markers = dessert_sweet_markers
        savory_pancake_markers = [
            "egg","bacon","ham","cheese","scallion","spring onion","kimchi","tuna",
            "chicken","beef","pork","shrimp","savory","pajeon","jeon","banh khot",
            "okonomiyaki","turmeric","coconut","fish sauce"
        ]
        if any(m in s for m in sweet_pancake_markers) and not any(m in s for m in savory_pancake_markers):
            role, rtype = "dessert", "dessert"
        else:
            role, rtype = "side", "side"
        forced_role = True

    # Drinks (explicit keywords)
    if not forced_role and (any(k in s for k in drink_kw) or has_word("drink")):
        role, rtype = "drink", "drink"
        forced_role = True

    # Desserts (explicit keywords) - with strong safeguards
    if not forced_role:
        is_savory_custard = ("custard" in s) and any(m in s for m in savory_custard_markers)
        is_savory_ricecake = any(m in s for m in savory_ricecake_markers)
        has_dessert_words = any(k in s for k in dessert_kw) or has_word("dessert") or has_word("desserts")
        has_cake_word = any(k in s for k in dessert_cake_kw) or has_word("cake") or has_word("cakes")
        # If it says "cake" but also "rice cake"/tteok -> do not treat as dessert
        if (has_dessert_words or (has_cake_word and any(m in s for m in dessert_sweet_markers))) and (not is_savory_custard) and (not is_savory_ricecake):
            role, rtype = "dessert", "dessert"
            forced_role = True


    if not forced_role and ("-sideorder-" in rid or "sideorder" in rid or has_word("sideorder")):
        role, rtype = "side", "side"
    elif not forced_role and ("-baguette-" in rid or "baguette" in rid or "banh-mi" in rid or has_word("baguette") or has_word("sandwich")
          or "wrap" in rid or has_word("wrap") or has_word("panini") or has_word("sub")):
        role, rtype = "handheld", "handheld"
    elif any(k in s for k in drink_kw) or has_word("drink"):
        role, rtype = "drink", "drink"
    elif (any(k in s for k in dessert_kw) or has_word("dessert")) and not (("custard" in s) and any(m in s for m in savory_custard_markers)) and not any(m in s for m in savory_ricecake_markers):
        role, rtype = "dessert", "dessert"
    else:
        # Heaviness for mains (used in combo logic)
        heavy_markers = [
            "curry","stew","braised","rendang","kaldereta","biryani","massaman","butter chicken",
            "katsu curry","ramen","laksa","pho","bo kho","bourguignon",
        ]
        if any(m in s for m in heavy_markers):
            role = "main_heavy"
        else:
            role = "main_light"

    # --- use-case ----------------------------------------------------------
    use_case: list[str] = []
    if any(k in s for k in ["lunch","office"]):
        use_case.append("lunch")
    if "breakfast" in s:
        use_case.append("breakfast")
    if any(k in s for k in ["family","barkada"]):
        use_case.append("family")
    if any(k in s for k in ["party","event","catering","tray"]):
        use_case.append("event")
    if not use_case:
        use_case = ["hero"]

    # --- protein -----------------------------------------------------------
    protein = "unknown"
    for p in ["chicken","beef","pork","shrimp","prawn","fish","salmon","tuna","tofu","veg","vegetable"]:
        if p in s:
            protein = "seafood" if p in ("shrimp","prawn","fish","salmon","tuna") else ("veg" if p in ("veg","vegetable") else p)
            break

    return {
        "cuisines": sorted(set(cuisines)),
        "type": rtype,          # main/side/baguette/drink/dessert
        "role": role,           # main_heavy/main_light/side/baguette/drink/dessert
        "protein": protein,
        "use_case": sorted(set(use_case)),
    }



def _split_strategy(md: str) -> tuple[str, str]:
    """Split the markdown at the Strategy Layer header."""
    patterns = [
        "\n## Strategy Layer",
        "\n## Strategy Layer",
        "\n## Strategy Layer",
        "\n# Strategy Layer",
    ]
    for p in patterns:
        idx = md.find(p)
        if idx != -1:
            return md[:idx].rstrip() + "\n", md[idx:].lstrip("\n")
    return md, ""



def _clean_title_md(title: str) -> str:
    """Clean title for use inside the markdown card itself (light-touch).
    We only remove RiceMap24 suffixes that don't belong to the dish name.
    """
    import re
    t = (title or "").strip()
    t = re.sub(r"\s+—\s+RiceMap24\s+.*?Recipe\s+Card\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+—\s+RiceMap24\s+.*?$", "", t, flags=re.IGNORECASE)
    return t.strip()


def _clean_title_display(title: str) -> str:
    """Clean title for the *UI header and recipe list*.

    - Remove non-Latin/Asian characters (JP/CN/TH/KR).
    - Remove metadata parentheses that aren't part of the dish name
      (e.g. '(Asian Twist, Side or Main, แกง...)', '"Banker Dish" for Home Kitchens').
    - Keep simple dish clarifiers like '(Crispy Fried Chicken)'.
    """
    import re

    t = _clean_title_md(title)

    # Strip common non-Latin ranges (Japanese, Chinese, Thai, Hangul)
    t = re.sub(r"[\u3040-\u30FF\u31F0-\u31FF\u3400-\u4DBF\u4E00-\u9FFF\u0E00-\u0E7F\uAC00-\uD7AF]", "", t)

    # Remove quoted marketing metadata chunks
    t = re.sub(r"\s+—\s+\"?Banker\s+Dish\"?\s+for\s+Home\s+Kitchens\s*$", "", t, flags=re.IGNORECASE)

    # Remove double-parenthesis blocks ((...)) that are clearly metadata
    def _drop_meta_parens(s: str) -> str:
        # First handle double-parens
        s = re.sub(r"\(\((.*?)\)\)", "", s)

        # Then selectively remove (...) blocks:
        # Keep if it's a short, simple clarifier without commas and without meta keywords.
        meta_keywords = ["asian twist", "side or main", "banker dish", "home kitchens", "concept", "premium"]
        def repl(m):
            inner = (m.group(1) or "").strip()
            low = inner.lower()
            if any(k in low for k in meta_keywords):
                return ""
            if any(ch in inner for ch in [",", ";", "/"]):
                return ""
            # If it still contains non-latin after earlier strip, drop
            if re.search(r"[\u3040-\u30FF\u31F0-\u31FF\u3400-\u4DBF\u4E00-\u9FFF\u0E00-\u0E7F\uAC00-\uD7AF]", inner):
                return ""
            # Keep short clarifiers like '(Crispy Fried Chicken)'
            if 0 < len(inner) <= 40:
                return f" ({inner})"
            return ""

        s = re.sub(r"\(([^)]*)\)", repl, s)
        return s

    t = _drop_meta_parens(t)

    # Clean leftover separators
    t = re.sub(r"\s{2,}", " ", t).strip()
    t = re.sub(r"\s+—\s+", " — ", t).strip()
    t = t.strip("-–— ")
    return t.strip()

def _clean_recipe_md(md: str) -> str:
    """Normalize recipe markdown for cleaner in-app reading."""
    import re
    text = (md or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    # Remove horizontal rules like '---' used as visual separators.
    lines = [ln for ln in lines if not re.match(r"^\s*---\s*$", ln)]

    # Collect any external links / source references and move them to the very end.
    # We intentionally support multiple formats across the recipe set:
    # - "Source recipe: ..." + URL on next line
    # - standalone URL lines anywhere in the document
    # - markdown links on their own line: [Title](https://...)
    # - an existing "## Source" section (we re-home it to the bottom)
    src_block: list[str] = []
    out_lines: list[str] = []
    i = 0
    # Match various "Source recipe" formats, including markdown bold and variants like
    # "Source recipe (reference):" or "**Source recipe:**".
    source_re = re.compile(r"^\s*(?:\*\*|__)?\s*Source\s+recipes?\b.*?:\s*", re.IGNORECASE)
    source_heading_re = re.compile(r"^\s*#{2,6}\s+Source\b", re.IGNORECASE)
    url_line_re = re.compile(r"^\s*(?:[-*]\s*)?(https?://\S+)\s*$", re.IGNORECASE)
    mdlink_line_re = re.compile(r"^\s*(?:[-*]\s*)?\[[^\]]+\]\((https?://[^)]+)\)\s*$", re.IGNORECASE)

    while i < len(lines):
        ln = lines[i]

        # If the file already contains a "## Source" section somewhere, capture it and
        # skip it from its current position (we will append it at the end).
        if source_heading_re.match(ln):
            src_block.append(ln.strip())
            j = i + 1
            while j < len(lines):
                if re.match(r"^\s*#{1,6}\s+\S", lines[j]):
                    break
                if lines[j].strip():
                    src_block.append(lines[j].rstrip())
                j += 1
            i = j
            continue
        if source_re.match(ln):
            src_block.append(ln.strip())
            j = i + 1
            while j < len(lines) and lines[j].strip():
                if re.match(r"^https?://", lines[j].strip(), flags=re.IGNORECASE) or len(lines[j].strip()) < 200:
                    src_block.append(lines[j].strip())
                j += 1
            i = j
            while i < len(lines) and not lines[i].strip():
                i += 1
            continue

        # Standalone URL or markdown link lines anywhere: move to Source.
        m_url = url_line_re.match(ln)
        if m_url:
            url = (m_url.group(1) or "").strip()
            if url:
                src_block.append(url)
            i += 1
            continue
        m_md = mdlink_line_re.match(ln)
        if m_md:
            url = (m_md.group(1) or "").strip()
            if url:
                src_block.append(url)
            i += 1
            continue

        out_lines.append(ln)
        i += 1

    # Clean title line (# ...)
    for k in range(min(5, len(out_lines))):
        if out_lines[k].startswith("# "):
            out_lines[k] = "# " + _clean_title_md(out_lines[k][2:].strip())
            break

    # Collapse multiple blank lines to max one.
    cleaned: list[str] = []
    blank = False
    for ln in out_lines:
        if not ln.strip():
            if not blank:
                cleaned.append("")
            blank = True
        else:
            cleaned.append(ln.rstrip())
            blank = False

    text2 = "\n".join(cleaned).strip() + "\n"

    # Normalize & append sources at bottom.
    if src_block:
        seen = set()
        normalized: list[str] = []
        for x in src_block:
            v = (x or "").strip()
            if not v:
                continue
            if v.lower().startswith("source recipe") or v.lower().startswith("source recipes"):
                vv = re.sub(r"\s+", " ", v)
            else:
                vv = v
            key = vv.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(vv)

        has_heading = any(source_heading_re.match(x) for x in normalized)
        if not has_heading:
            normalized.insert(0, "## Source")

        text2 = text2.rstrip() + "\n\n" + "\n".join(normalized).strip() + "\n"
    return text2


def _stable_hash(s: str) -> int:
    """Deterministic small hash for stable suggestions (no randomness)."""
    import hashlib
    h = hashlib.sha256(s.encode('utf-8', errors='ignore')).hexdigest()
    return int(h[:8], 16)


def _pick(stable_seed: str, items: list[str], k: int = 2) -> list[str]:
    if not items:
        return []
    h = _stable_hash(stable_seed)
    start = h % len(items)
    out: list[str] = []
    for i in range(len(items)):
        out.append(items[(start + i) % len(items)])
        if len(out) >= k:
            break
    return out


def _guess_role(meta: dict, recipe_id: str) -> str:
    tags = (meta or {}).get('tags') or {}
    t = str(tags.get('type') or tags.get('role') or '').lower()
    rid = str(recipe_id or '').lower()
    title = str((meta or {}).get('title') or '').lower()
    text = f"{rid} {title} {t}"

    # handhelds
    if any(x in text for x in ['baguette', 'banh mi', 'banh-mi', 'wrap', 'sandwich', 'panini', 'sub']):
        return 'handheld'
    # drinks
    if any(x in text for x in ['iced tea', 'thai tea', 'lemonade', 'latte', 'coffee', 'smoothie', 'boba', 'juice', 'soda']):
        return 'drink'
    # desserts (require strong markers)
    if any(x in text for x in ['mochi', 'ice cream', 'gelato', 'tiramisu', 'brownie', 'cookie', 'pudding', 'dessert', 'nutella', 'syrup']):
        return 'dessert'
    # sides
    if any(x in text for x in ['sideorder', 'side order', 'spring roll', 'lumpia', 'dumpling', 'wonton', 'bao', 'fries', 'pickles', 'slaw', 'salad', 'dip', 'pajeon', 'banh khot', 'tteokbokki']):
        return 'side'
    # heavy mains
    if any(x in text for x in ['curry', 'stew', 'banker dish', 'braise']):
        return 'main_heavy'
    return 'main'


def _generate_strategy_md(meta: dict, recipe_md: str, recipe_id: str) -> str:
    """Generate a useful Strategy Layer when the recipe file doesn't include one."""
    title = (meta or {}).get('title') or recipe_id
    role = _guess_role(meta, recipe_id)

    if role == 'main_heavy':
        sides = ["Fresh cucumber/pickles side (adds crunch)", "Light salad/slaw to balance richness", "Extra sauce cup + jasmine rice"]
        drinks = ["Thai iced tea", "Lime soda", "Iced lemon tea"]
        desserts = ["Mango sticky rice", "Coconut pudding", "Mochi"]
        campaign = ["Monthly special: rich comfort bowl", "Limited Friday batch (pre-order)"]
        copy = ["Comforting, rich, and deeply savory.", "Slow-simmered flavor with a silky sauce — perfect for a cozy dinner."]
        ops = ["Best served hot. Offer 'extra sauce cup' upsell.", "Hold time: 2–3 hours warm. Keep garnish separate."]
    elif role == 'handheld':
        sides = ["Crispy side (spring rolls / fries)", "Pickles/slaw cup", "Extra dipping sauce cup"]
        drinks = ["Iced coffee", "Thai iced tea", "Lemonade"]
        desserts = ["Cookie/brownie add-on", "Mochi", "Coconut pudding"]
        campaign = ["Lunch deal: handheld + drink", "Office lunch pack (10+ orders)"]
        copy = ["A bold, satisfying handheld with a clean finish.", "Perfect for lunch — add a drink to make it a set."]
        ops = ["Pack sauce separately. Vent crispy parts.", "Heat-at-home option: toast bread 3–4 min for best crunch."]
    elif role == 'side':
        sides = ["Pair with a lighter main", "Add a fresh/cold side for balance", "Add a dipping sauce cup"]
        drinks = ["Lime soda", "Iced tea"]
        desserts = ["Mochi", "Coconut pudding"]
        campaign = ["Snack box: 2–3 sides", "Add-on upsell: extra dip"]
        copy = ["Crispy, snackable, and easy to share.", "Perfect as a side or a small bite on the go."]
        ops = ["Keep crispy items vented.", "Hold time: best within 60–90 min."]
    elif role == 'drink':
        sides = ["Pairs well with handhelds", "Pairs well with spicy mains"]
        drinks = []
        desserts = ["Cookie/brownie", "Mochi"]
        campaign = ["Add-on: drink upgrade", "Morning/lunch drink special"]
        copy = ["Refreshing and easy to bundle.", "Great as an add-on to lift order value."]
        ops = ["Serve cold. Use sealed cups.", "Offer size upgrades (small/large)."]
    else:  # main
        sides = ["Fresh side (salad/slaw/pickles)", "Crispy side (spring rolls)", "Extra sauce cup"]
        drinks = ["Lime soda", "Iced tea", "Thai iced tea"]
        desserts = ["Mochi", "Coconut pudding", "Fruit add-on"]
        campaign = ["Lunch bowl special", "Tasting set: 2 light dishes"]
        copy = ["Bright, balanced flavors with a clean finish.", "A lighter main that pairs well with a small side."]
        ops = ["Hold time: 1–2 hours warm.", "Keep crunchy toppings separate."]

    seed = f"{recipe_id}:{title}"
    pick_sides = _pick(seed+":sides", sides, 2)
    pick_drinks = _pick(seed+":drinks", drinks, 2)
    pick_dess = _pick(seed+":dess", desserts, 2)
    pick_camp = _pick(seed+":camp", campaign, 2)
    pick_ops = _pick(seed+":ops", ops, 2)

    lines: list[str] = []
    lines.append("## Strategy Layer")
    lines.append("")
    lines.append("### Best use case")
    if role == 'main_heavy':
        lines.append("- Hero dish / comfort main")
    elif role == 'handheld':
        lines.append("- Lunch / office-friendly set")
    elif role == 'side':
        lines.append("- Side order / shareable bite")
    elif role == 'drink':
        lines.append("- Add-on to lift order value")
    elif role == 'dessert':
        lines.append("- Finish / sweet add-on")
    else:
        lines.append("- Light main (pairs well with sides)")

    lines.append("")
    lines.append("### Winning combos (add-ons)")
    for s in pick_sides:
        lines.append(f"- Side: {s}")
    for d in pick_drinks:
        lines.append(f"- Drink: {d}")
    for de in pick_dess:
        lines.append(f"- Dessert: {de}")

    lines.append("")
    lines.append("### Campaign angles")
    for c in pick_camp:
        lines.append(f"- {c}")

    lines.append("")
    lines.append("### Marketing copy")
    lines.append(f"- One-liner: {copy[0]}")
    lines.append(f"- 2–3 lines: {copy[1]}")
    lines.append("- Upsell line: Add an extra sauce cup / side to make it a set.")

    lines.append("")
    lines.append("### Packaging & delivery notes")
    for o in pick_ops:
        lines.append(f"- {o}")

    return "\n".join(lines).strip() + "\n"


def _generate_strategy_md_from_related(meta: dict, recipe_md: str, recipe_id: str, rel: dict) -> str:
    """Generate Strategy Layer using *actual* library recipes when possible.

    If the library contains matching side/drink/dessert recipes (as chosen by _related_recipe_ids),
    we reference those titles here so Strategy and Combos stay consistent.
    """
    # Start with the normal template (deterministic), but replace combo lines with linked library picks.
    base = _generate_strategy_md(meta, recipe_md, recipe_id)

    addons_ids = list(rel.get("addons") or [])
    def _by_type(t: str) -> list[str]:
        out: list[str] = []
        for rid in addons_ids:
            r = _RECIPES_INDEX.get(rid) or {}
            rt = str((r.get("tags") or {}).get("type") or "")
            if rt == t:
                out.append(rid)
        return out

    side_ids = _by_type("side")
    drink_ids = _by_type("drink")
    dessert_ids = _by_type("dessert")

    # If we have no library drinks/desserts, fall back to generic suggestions for those parts.
    generic = rel.get("generic_addons") or []

    # Build a replacement "Winning combos" section.
    lines: list[str] = []
    lines.append("## Strategy Layer")
    lines.append("")

    # Reuse Best use case from base (keep it simple and stable)
    # Extract the first bullet under "Best use case" from base.
    best_use = "- Hero dish / comfort main"
    try:
        for bl in base.split("\n"):
            if bl.strip().startswith("-") and "use case" not in bl.lower():
                best_use = bl.strip()
                break
    except Exception:
        pass

    lines.append("### Best use case")
    lines.append(best_use)
    lines.append("")

    lines.append("### Winning combos (add-ons)")
    lines.append("")
    lines.append("**From your recipe library (clickable in the Combos tab):**")

    had_library = False
    if side_ids:
        had_library = True
        for rid in side_ids[:2]:
            lines.append(f"- Side: {_RECIPES_INDEX.get(rid, {}).get('title') or rid}")
    if drink_ids:
        had_library = True
        for rid in drink_ids[:2]:
            lines.append(f"- Drink: {_RECIPES_INDEX.get(rid, {}).get('title') or rid}")
    if dessert_ids:
        had_library = True
        for rid in dessert_ids[:2]:
            lines.append(f"- Dessert: {_RECIPES_INDEX.get(rid, {}).get('title') or rid}")

    if not had_library:
        lines.append("- (No matching add-on recipes found yet)")

    # Always include helpful non-library suggestions (masterchef-style balance + sales upsells).
    if generic:
        lines.append("")
        lines.append("**Suggested extras (not in your library):**")
        for g in generic[:6]:
            lines.append(f"- {g}")

    # Append the remaining sections from base after "Winning combos".
    # Keep everything from "Campaign angles" onwards.
    keep = []
    in_keep = False
    for bl in base.split("\n"):
        if bl.strip().lower().startswith("### campaign angles"):
            in_keep = True
        if in_keep:
            keep.append(bl)
    if keep:
        lines.append("")
        lines.extend(keep)

    return "\n".join(lines).strip() + "\n"

def _md_to_html(md: str) -> str:
    """Tiny markdown renderer (headings, bold/italic, lists, code fences)."""
    import html
    import re

    out: list[str] = []
    text = md.replace("\r\n", "\n").replace("\r", "\n")
    # Strip internal/source notes embedded as HTML comments in the markdown.
    # These are meant for internal attribution only and must not show in UI.
    text = re.sub(r"<!--\s*RICEMAP24_INTERNAL.*?-->", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Also strip any remaining HTML comments to avoid leaking placeholders.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    lines = text.split("\n")
    in_ul = False
    in_code = False

    for raw in lines:
        line = raw.rstrip("\n")

        if line.strip().startswith("```"):
            if not in_code:
                out.append('<pre class="md-code"><code>')
                in_code = True
            else:
                out.append('</code></pre>')
                in_code = False
            continue

        if in_code:
            out.append(html.escape(line))
            continue

        if line.startswith("### "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h3>{html.escape(line[4:].strip())}</h3>")
            continue
        if line.startswith("## "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
            continue
        if line.startswith("# "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
            continue

        if line.lstrip().startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            li = html.escape(line.lstrip()[2:])
            # Use regex backreferences correctly; do not double-escape.
            li = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", li)
            li = re.sub(r"\*(.+?)\*", r"<em>\1</em>", li)
            out.append(f"<li>{li}</li>")
            continue
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False

        if not line.strip():
            continue

        p = html.escape(line)
        # NOTE: Use regex backreferences (\1) in replacement strings.
        # Do NOT double-escape (\\1) or the UI will literally show "\1".
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"\*(.+?)\*", r"<em>\1</em>", p)
        out.append(f"<p>{p}</p>")

    if in_ul:
        out.append("</ul>")
    if in_code:
        out.append("</code></pre>")

    return "\n".join(out)


def _load_recipes_index() -> None:
    global _RECIPES_INDEX, _RECIPES_ORDER, _TRIAL_IDS, _STANDARD_STRATEGY_IDS

    files = sorted([p for p in RECIPES_DIR.rglob("*.md") if p.is_file() and "__MACOSX" not in str(p)])
    idx: dict[str, dict] = {}

    for p in files:
        rid = p.stem
        md_raw = p.read_text(encoding="utf-8", errors="replace")

        # Extract raw title from the original file (so the in-card title can remain rich),
        # but the UI list/header uses a cleaned display title.
        raw_title = rid
        for line in md_raw.split("\n"):
            if line.startswith("# "):
                raw_title = line[2:].strip()
                break

        md = _clean_recipe_md(md_raw)

        title = _clean_title_display(raw_title)

        teaser = ""
        raw_lines = [l.strip() for l in md.split("\n")]
        try:
            i0 = next(i for i, l in enumerate(raw_lines) if l.startswith("# "))
        except StopIteration:
            i0 = 0
        for j in range(i0 + 1, min(i0 + 12, len(raw_lines))):
            if raw_lines[j] and not raw_lines[j].startswith(">") and not raw_lines[j].startswith("<!--"):
                teaser = raw_lines[j]
                break

        idx[rid] = {
            "id": rid,
            "title": title,
            "title_full": _clean_title_md(raw_title),
            "title_raw": raw_title,
            "teaser": teaser,
            "path": str(p),
            "tags": _infer_tags(rid, raw_title),
        }

    order = sorted(idx.keys(), key=lambda k: (_stable_int(k), k))

    trial_ids = set(order[: min(6, len(order))])
    standard_strategy_ids = set([k for k in order if (_stable_int(k) % 100) < 35])

    _RECIPES_INDEX = idx
    _RECIPES_ORDER = order
    _TRIAL_IDS = trial_ids
    _STANDARD_STRATEGY_IDS = standard_strategy_ids


def _recipe_access(plan: str, recipe_id: str) -> dict:
    plan = _normalize_plan(plan)

    if plan in ("growth", "pro"):
        return {"can_open": True, "show_strategy": True, "tier": plan}

    if plan == "business":
        # Business has menu/recipe access, but not the strategy layer.
        return {"can_open": True, "show_strategy": False, "tier": "business"}

    # Basic has no Recipe Library access.
    return {"can_open": False, "show_strategy": False, "tier": "basic"}


def _generic_addons_for(tags: dict) -> list[str]:
    """Fallback add-ons when the library lacks proper side/drink/dessert items.

    These are *generic menu suggestions*, not recipe links.
    """
    role = str((tags or {}).get("role") or (tags or {}).get("type") or "main").lower()
    base = ["Extra sauce cup", "Spice level option (mild/medium/hot)"]

    if role == "baguette":
        return [
            "Side: fries / crispy side",
            "Side: fresh slaw or pickles (balance)",
            "Drink: iced tea / lemonade",
            "Dessert: small sweet (optional)",
            *base,
        ][:6]
    if role in ("main_heavy", "main"):
        return [
            "Side: cucumber/pickles or fresh salad (balance)",
            "Extra: rice portion / extra gravy cup",
            "Drink: iced tea / soda",
            "Dessert: light sweet (optional)",
            *base,
        ][:6]
    if role == "main_light":
        return [
            "Add a small side (crispy or fresh)",
            "Drink: iced tea / coffee",
            "Dessert: optional",
            *base,
        ][:6]
    if role == "side":
        return [
            "Pair with a main dish",
            "Drink: iced tea",
            "Extra sauce cup",
        ][:6]
    if role == "drink":
        return [
            "Pair with a baguette or light main",
            "Add a small sweet",
        ][:6]
    if role == "dessert":
        return ["Pair with coffee/tea"]
    return base[:6]


def _related_recipe_ids(recipe_id: str, n_addons: int = 4, n_similar: int = 6) -> dict:
    """Deterministic, menu-logical suggestions.

    - Recommended add-ons should look like a real menu: sides/drinks/desserts.
    - Similar recipes can show other mains.
    """
    cur = _RECIPES_INDEX.get(recipe_id)
    if not cur:
        return {"addons": [], "similar": [], "generic_addons": []}

    tags = cur.get("tags") or {}
    cuisines = set(tags.get("cuisines") or [])
    rtype = str(tags.get("type") or "main")
    role = str(tags.get("role") or rtype)
    use_case = set(tags.get("use_case") or [])

    stop = {
        "ricemap24","standard","premium","recipe","card","home","kitchen","concepts","vol",
        "the","and","with","of","style","best","easy","quick","classic","special",
        "breakfast","lunch","dinner","family","party","event",
    }

    def _tokens(s: str) -> set[str]:
        import re
        s = (s or "").lower()
        s = re.sub(r"[^a-z0-9\-\s]", " ", s)
        return {t.strip("-") for t in s.split() if t and t not in stop and len(t) > 2}

    cur_tokens = _tokens((cur.get("title") or "") + " " + recipe_id)

    def score(other_id: str) -> int:
        o = _RECIPES_INDEX.get(other_id) or {}
        t = (o.get("tags") or {})
        s = 0
        if cuisines.intersection(set(t.get("cuisines") or [])):
            s += 3
        if use_case.intersection(set(t.get("use_case") or [])):
            s += 2
        if str(t.get("type") or "") == rtype:
            s += 1
        ot = _tokens((o.get("title") or "") + " " + other_id)
        overlap = len(cur_tokens.intersection(ot))
        if overlap:
            s += min(4, overlap)
        return s

    def _pick_by_type(target_type: str, limit: int) -> list[str]:
        cand = [
            k for k in _RECIPES_ORDER
            if k != recipe_id and str((_RECIPES_INDEX.get(k, {}).get("tags") or {}).get("type") or "") == target_type
        ]
        cand = sorted(cand, key=lambda k: (-score(k), _stable_int(k)))
        return cand[:limit]

    addons: list[str] = []
    # Always provide generic add-on ideas (not linked to recipes).
    # These can be shown under Strategy and optionally as "Suggested extras" in Combos.
    generic_addons: list[str] = _generic_addons_for(tags)

    # Menu-logic: build a *balanced* add-on set so it feels like a real menu.
    # For mains/handhelds: typically 2 sides + 1 drink + 1 dessert.
    if role in ("main_heavy", "main_light", "main", "baguette"):
        target_mix = [("side", 2), ("drink", 1), ("dessert", 1)]
        disallow_types = {"main", "baguette"}
    elif role == "side":
        target_mix = [("main", 2), ("drink", 1), ("dessert", 1)]
        disallow_types = set()
    elif role == "drink":
        # A drink should pair with handhelds/sides/desserts, not random mains.
        target_mix = [("dessert", 1), ("baguette", 1), ("side", 1)]
        disallow_types = {"main"}
    elif role == "dessert":
        # Desserts should NOT recommend mains as "add-ons".
        # Keep it cafe-like: drinks + optionally a light side/snack.
        target_mix = [("drink", 2), ("dessert", 1), ("side", 1)]
        disallow_types = {"main", "baguette"}
    else:
        target_mix = [("side", 2), ("drink", 1), ("dessert", 1)]
        disallow_types = {"main", "baguette"}

    def _count_type(tid: str) -> int:
        return len([x for x in addons if str((_RECIPES_INDEX.get(x, {}).get("tags") or {}).get("type") or "") == tid])

    for tid, need in target_mix:
        if len(addons) >= n_addons:
            break
        for c in _pick_by_type(tid, limit=max(need * 3, n_addons)):
            if c not in addons:
                addons.append(c)
            if _count_type(tid) >= need:
                break
        if len(addons) >= n_addons:
            break

    # Fill remaining slots (if needed), but never violate disallow_types.
    if len(addons) < n_addons:
        cand_fb = [k for k in _RECIPES_ORDER if k != recipe_id and k not in addons]
        cand_fb = sorted(cand_fb, key=lambda k: (-score(k), _stable_int(k)))
        for c in cand_fb:
            t = str((_RECIPES_INDEX.get(c, {}).get("tags") or {}).get("type") or "")
            if t in disallow_types:
                continue
            addons.append(c)
            if len(addons) >= n_addons:
                break

    addons = addons[:n_addons]

    cand2 = [k for k in _RECIPES_ORDER if k != recipe_id]
    cand2 = sorted(cand2, key=lambda k: (-score(k), _stable_int(k)))

    # Role-aware "Similar": keep it sensible.
    # - Desserts should show desserts (and maybe drinks), not mains.
    # - Drinks should show drinks/desserts/handhelds, not mains.
    if role == "dessert":
        allowed_similar_types = {"dessert", "drink"}
        disallow_similar_types = {"main", "baguette"}
    elif role == "drink":
        allowed_similar_types = {"drink", "dessert", "baguette", "side"}
        disallow_similar_types = {"main"}
    elif role == "side":
        allowed_similar_types = {"side", "main", "baguette"}
        disallow_similar_types = set()
    else:
        allowed_similar_types = set()  # no strict allowlist
        disallow_similar_types = set()

    similar: list[str] = []
    for k in cand2:
        if k in addons:
            continue
        t = str((_RECIPES_INDEX.get(k, {}).get("tags") or {}).get("type") or "")
        if allowed_similar_types and t not in allowed_similar_types:
            continue
        if disallow_similar_types and t in disallow_similar_types:
            continue
        similar.append(k)
        if len(similar) >= n_similar:
            break

    # Fallback: if strict filtering produced too few, fill with best matches but keep disallows.
    if len(similar) < max(3, min(6, n_similar)):
        for k in cand2:
            if k in addons or k in similar:
                continue
            t = str((_RECIPES_INDEX.get(k, {}).get("tags") or {}).get("type") or "")
            if disallow_similar_types and t in disallow_similar_types:
                continue
            similar.append(k)
            if len(similar) >= n_similar:
                break

    return {"addons": addons, "similar": similar, "generic_addons": generic_addons}

def _resolve_public_image_path(path_str: str) -> Optional[Path]:
    """Resolve a listing image path to a local file.

    Supports:
      - web/public/assets/*  (e.g. "assets/hero_filipino_tb.jpg")
      - uploads/*            (future)
    """
    if not path_str:
        return None
    p = path_str.strip().lstrip("/")
    # uploads
    if p.startswith("uploads/"):
        cand = (UPLOADS_DIR / p.replace("uploads/", "", 1)).resolve()
        if str(cand).startswith(str(UPLOADS_DIR)) and cand.exists():
            return cand
        return None
    # default: web/public
    cand = (WEB_PUBLIC / p).resolve()
    if str(cand).startswith(str(WEB_PUBLIC)) and cand.exists():
        return cand
    return None


def _normalize_cover_source(img: Image.Image) -> Image.Image:
    """Normalize uploaded images before any cover-crop math.

    This prevents EXIF-rotated images from looking stretched/squashed in poster frames.
    """
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def _cover_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Crop+resize like CSS background-size: cover, never stretch to fit."""
    img = _normalize_cover_source(img)
    iw, ih = img.size
    if iw <= 0 or ih <= 0:
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    target_ratio = max(0.01, target_w / float(max(1, target_h)))
    src_ratio = iw / float(max(1, ih))

    if src_ratio > target_ratio:
        # wider than target -> crop sides
        new_w = max(1, int(round(ih * target_ratio)))
        x0 = max(0, (iw - new_w) // 2)
        img = img.crop((x0, 0, x0 + new_w, ih))
    else:
        # taller than target -> crop top/bottom
        new_h = max(1, int(round(iw / target_ratio)))
        y0 = max(0, (ih - new_h) // 2)
        img = img.crop((0, y0, iw, y0 + new_h))

    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


def _cover_crop_adjusted(img: Image.Image, target_w: int, target_h: int, focal_x: float = 50, focal_y: float = 50, zoom: float = 100) -> Image.Image:
    """CSS-like cover crop with focal point + zoom, without ever distorting aspect ratio."""
    img = _normalize_cover_source(img)
    iw, ih = img.size
    if iw <= 0 or ih <= 0:
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    target_ratio = max(0.01, target_w / float(max(1, target_h)))
    src_ratio = iw / float(max(1, ih))
    if src_ratio >= target_ratio:
        base_h = ih
        base_w = ih * target_ratio
    else:
        base_w = iw
        base_h = iw / target_ratio
    zoom = max(100.0, min(200.0, float(zoom or 100)))
    crop_w = max(1, min(iw, int(round(base_w * (100.0 / zoom)))))
    crop_h = max(1, min(ih, int(round(base_h * (100.0 / zoom)))))
    fx = max(0.0, min(100.0, float(focal_x if focal_x is not None else 50.0))) / 100.0
    fy = max(0.0, min(100.0, float(focal_y if focal_y is not None else 50.0))) / 100.0
    x0 = int(round((iw - crop_w) * fx))
    y0 = int(round((ih - crop_h) * fy))
    x0 = max(0, min(iw - crop_w, x0))
    y0 = max(0, min(ih - crop_h, y0))
    cropped = img.crop((x0, y0, x0 + crop_w, y0 + crop_h))
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def _poster_tagline(listing: dict, lang: str) -> str:
    intro = listing.get("intro") or {}
    if isinstance(intro, dict):
        s = (intro.get(lang) or intro.get("en") or intro.get("no") or "").strip()
        if s:
            return s
    # fallback
    return "Homemade food — fresh, local, and made with care."


@app.get("/api/owner/{token}/qr.png")
def owner_qr_png(token: str, request: Request, download: int = 0):
    # Token is normally a preview_token. For demo convenience, also accept a slug
    # for *published* listings.
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    url = _public_listing_url(request, listing["slug"])

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    headers = {}
    if int(download or 0) == 1:
        headers['Content-Disposition'] = f'attachment; filename="{listing['slug']}-qr.png"'
    return Response(content=buf.getvalue(), media_type="image/png", headers=headers)


@app.get("/api/owner/{token}/poster.pdf")
def owner_poster_pdf(token: str, request: Request, download: int = 1):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')

    url = _public_listing_url(request, listing["slug"])

    # Build QR image (PIL)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")

    # PDF (A4)
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4

    # Frame
    margin = 16 * mm
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Header
    title = listing.get("name") or "Kitchen"
    subtitle = f"{listing.get('area','')} · {listing.get('city','')}".strip(" ·")
    c.setFillColorRGB(0.08, 0.10, 0.12)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(margin, H - margin - 10, title)

    if subtitle:
        c.setFillColorRGB(0.35, 0.38, 0.42)
        c.setFont("Helvetica", 12)
        c.drawString(margin, H - margin - 34, subtitle)

    # CTA
    c.setFillColorRGB(0.08, 0.10, 0.12)
    c.setFont("Helvetica", 14)
    c.drawString(margin, H - margin - 62, "Scan to view menu and order")

    # QR placement
    qr_size = 92 * mm
    qr_x = (W - qr_size) / 2
    qr_y = (H / 2) - (qr_size / 2) + 8 * mm
    c.drawImage(ImageReader(qr_img), qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")

    # URL footer
    c.setFillColorRGB(0.35, 0.38, 0.42)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W / 2, qr_y - 14 * mm, url)

    c.showPage()
    c.save()

    pdf.seek(0)
    return _pdf_stream_response(pdf, f"{listing['slug']}-poster.pdf", download=download)


@app.get("/api/owner/{token}/promo-poster.pdf")
def owner_promo_poster_pdf(
    token: str,
    request: Request,
    lang: str = "en",
    download: int = 1,
    headline: str = "",
    support: str = "",
    hero_focal_x: float | None = None,
    hero_focal_y: float | None = None,
    hero_zoom: float | None = None,
    accent_color: str = "",
    ink_color: str = "",
    title_color: str = "",
    title_size: float | None = None,
    band_color: str = "",
    bg_color: str = "",
):
    """A4 promo poster built from the kitchen page: hero, sales text, kitchen copy, signature dish and QR."""
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')

    lang = (lang or "en").lower().strip()
    if lang not in ("en", "no"):
        lang = "en"

    url = _public_listing_url(request, listing["slug"])

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")

    hero_path = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    if not hero_path:
        hero_path = _resolve_public_image_path("assets/portal_hero.jpg")
    sig_img_path = _signature_image_path(listing)

    hero = None
    sig_img = None
    try:
        if hero_path and hero_path.exists():
            hero = Image.open(str(hero_path)).convert("RGB")
    except Exception:
        hero = None
    try:
        if sig_img_path and sig_img_path.exists():
            sig_img = Image.open(str(sig_img_path)).convert("RGB")
    except Exception:
        sig_img = None

    title = (listing.get("name") or "Kitchen").strip()
    subtitle_bits = []
    area = str(listing.get('area') or '').strip()
    city = str(listing.get('city') or '').strip()
    if area:
        subtitle_bits.append(area)
    if city and city.lower() not in {x.lower() for x in subtitle_bits}:
        subtitle_bits.append(city)
    subtitle = " · ".join([x for x in subtitle_bits if x])

    default_headline = " ".join(_flyer_headline_lines(listing, lang)).strip()
    headline = (headline or default_headline or ("Fresh homemade food, ready to order" if lang == "en" else "Fersk hjemmelaget mat, klar til bestilling")).strip()
    if not (headline or "").strip():
        headline = "FRESH HOMEMADE FOOD, READY TO ORDER" if lang == "en" else "FERSK HJEMMELAGET MAT, KLAR TIL BESTILLING"
    else:
        headline = headline.upper()
    support = (support or _flyer_support_text(listing, lang) or "").strip()
    sig_title, sig_desc, _sig_price = _get_signature_dish(listing, lang)
    sig_title = (sig_title or ("Signature dish" if lang == "en" else "Signaturrett")).strip()
    cta = "Visit our kitchen and view our menu" if lang == "en" else "Besøk kjøkkenet vårt og se menyen"
    badge_label = "LOCAL ASIAN KITCHEN" if lang == "en" else "LOKALT ASIATISK KJØKKEN"
    sig_label = "Signature dish" if lang == "en" else "Signaturrett"
    about_label = "About our kitchen" if lang == "en" else "Om kjøkkenet"

    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4

    bg_hex = bg_color or "#f7f1e8"
    ink_hex = ink_color or "#161616"
    accent_hex = accent_color or "#aa5a3d"
    title_hex = title_color or "#ffffff"
    band_hex = band_color or "#3b241d"
    title_size = max(12.0, min(34.0, float(title_size or 22.0)))
    hero_focal_x = max(0.0, min(100.0, float(hero_focal_x if hero_focal_x is not None else 50.0)))
    hero_focal_y = max(0.0, min(100.0, float(hero_focal_y if hero_focal_y is not None else 50.0)))
    hero_zoom = max(100.0, min(200.0, float(hero_zoom if hero_zoom is not None else 100.0)))

    bg = colors.HexColor(bg_hex)
    ink = colors.HexColor(ink_hex)
    muted = colors.HexColor(_rgb01_to_hex(tuple(max(0.0, min(1.0, v*0.72 + 0.18)) for v in _hex_to_rgb01(ink_hex, (0.09,0.09,0.09))), '#625b54'))
    soft = colors.HexColor(_rgb01_to_hex(tuple(max(0.0, min(1.0, v*0.10 + 0.90)) for v in _hex_to_rgb01(bg_hex, (0.97,0.95,0.91))), '#fffaf4'))
    line = colors.HexColor(_rgb01_to_hex(tuple(max(0.0, min(1.0, v*0.20 + 0.80)) for v in _hex_to_rgb01(bg_hex, (0.92,0.87,0.83))), '#eadfd3'))
    accent = colors.HexColor(accent_hex)
    accent_soft = colors.HexColor(_rgb01_to_hex(tuple(max(0.0, min(1.0, v*0.18 + 0.82)) for v in _hex_to_rgb01(accent_hex, (0.66,0.35,0.24))), '#f3dfd4'))
    band_fill = colors.HexColor(band_hex)

    c.setFillColor(bg)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    outer = 10 * mm
    content_w = W - 2 * outer

    # Hero image, large and simple like the kitchen page.
    hero_h = 145 * mm
    hero_x = outer
    hero_y = H - outer - hero_h
    if hero is not None:
        try:
            hero2 = _cover_crop_adjusted(hero, max(1, int(content_w)), max(1, int(hero_h)), focal_x=hero_focal_x, focal_y=hero_focal_y, zoom=hero_zoom)
            c.drawImage(ImageReader(hero2), hero_x, hero_y, width=content_w, height=hero_h, mask="auto")
        except Exception:
            c.setFillColor(colors.HexColor("#e8dccf"))
            c.rect(hero_x, hero_y, content_w, hero_h, stroke=0, fill=1)
    else:
        c.setFillColor(colors.HexColor("#e8dccf"))
        c.rect(hero_x, hero_y, content_w, hero_h, stroke=0, fill=1)

    # Warm dark band at the bottom of the hero for title readability.
    # Make it a little slimmer and extend it a hair beyond the image bounds
    # to avoid any visible anti-aliased gap on the left edge.
    band_h = 16 * mm
    band_x = hero_x - 0.5
    band_w = content_w + 1.0
    band_y = hero_y + 6.5 * mm
    if hasattr(c, 'setFillAlpha'):
        c.saveState()
        c.setFillAlpha(0.12)
        c.setFillColor(accent)
        c.rect(band_x, band_y, band_w, band_h, stroke=0, fill=1)
        c.restoreState()
        c.saveState()
        c.setFillAlpha(0.72)
        c.setFillColor(band_fill)
        c.rect(band_x, band_y, band_w, band_h, stroke=0, fill=1)
        c.restoreState()
    else:
        c.setFillColor(band_fill)
        c.rect(band_x, band_y, band_w, band_h, stroke=0, fill=1)

    # Kitchen title on hero: centered in the dark band with a warmer italic display feel.
    title_text = title[:42]
    title_font = "Times-BoldItalic"
    title_w = stringWidth(title_text, title_font, title_size)
    title_x = hero_x + ((content_w - title_w) / 2)
    title_baseline = band_y + (band_h / 2) - (title_size * 0.18)
    c.setFillColor(colors.HexColor(title_hex))
    c.setFont(title_font, title_size)
    c.drawString(title_x, title_baseline, title_text)

    chip_font = 9.6
    chip_pad_x = 5.2 * mm
    chip_text_w = stringWidth(badge_label[:30], "Helvetica-Bold", chip_font)
    chip_w = chip_text_w + (chip_pad_x * 2)
    chip_h = 8.8 * mm
    chip_x = hero_x + 12
    chip_y = band_y + band_h + 4.5 * mm
    c.setFillColor(soft)
    c.setStrokeColor(accent_soft)
    c.roundRect(chip_x, chip_y, chip_w, chip_h, 7, stroke=1, fill=1)
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", chip_font)
    c.drawString(chip_x + chip_pad_x, chip_y + 3.15 * mm, badge_label[:30])

    # Lower content section.
    body_top = hero_y - 12 * mm
    left_w = content_w * 0.62
    text_right_margin = 15 * mm  # narrower text block so body copy keeps a clearer gap from the signature dish image
    gap = 8 * mm
    right_x = outer + left_w + gap
    right_w = content_w - left_w - gap
    sig_card_top = body_top + 2 * mm

    # Sales headline: uppercase by default and vertically aligned with the top of the signature image.
    headline_font = "Helvetica-Bold"
    headline_size = 25
    head_lines = _wrap_lines(headline, left_w - 4, headline_font, headline_size)
    headline_ascent = (pdfmetrics.getAscent(headline_font) / 1000.0) * headline_size
    head_top_y = sig_card_top
    head_y = head_top_y - headline_ascent
    c.setFillColor(ink)
    c.setFont(headline_font, headline_size)
    headline_leading = 11.0 * mm
    for i, ln in enumerate(head_lines[:3]):
        c.drawString(outer, head_y - i * headline_leading, ln)

    accent_y = head_y - max(1, len(head_lines[:3])) * headline_leading - 2.1 * mm
    c.setStrokeColor(accent)
    c.setLineWidth(1.2)
    c.line(outer, accent_y, outer + 26 * mm, accent_y)

    about_y = accent_y - 8 * mm
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 12.8)
    c.drawString(outer, about_y, about_label)

    support_lines = _wrap_lines(support, left_w - text_right_margin, "Helvetica", 12.6)
    c.setFillColor(muted)
    c.setFont("Helvetica", 14.0)
    support_start = about_y - 7.6 * mm
    for i, ln in enumerate(support_lines[:5]):
        c.drawString(outer, support_start - i * 6.8 * mm, ln)

    # Signature dish block on the right, visually tied to the kitchen page content.
    sig_img_h = 34 * mm
    sig_img_y = sig_card_top - sig_img_h
    if sig_img is not None:
        try:
            sig2 = _cover_crop(sig_img, max(1, int(right_w)), max(1, int(sig_img_h)))
            c.drawImage(ImageReader(sig2), right_x, sig_img_y, width=right_w, height=sig_img_h, mask="auto")
        except Exception:
            c.setFillColor(colors.HexColor("#e9dece"))
            c.rect(right_x, sig_img_y, right_w, sig_img_h, stroke=0, fill=1)
    else:
        c.setFillColor(colors.HexColor("#e9dece"))
        c.rect(right_x, sig_img_y, right_w, sig_img_h, stroke=0, fill=1)

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 8.8)
    c.drawString(right_x, sig_img_y - 5.5 * mm, sig_label)
    c.setFillColor(ink)
    c.setFont("Helvetica-Bold", 12)
    dish_name_y = sig_img_y - 11.5 * mm
    for i, ln in enumerate(_wrap_lines(sig_title, right_w, "Helvetica-Bold", 12)[:2]):
        c.drawString(right_x, dish_name_y - i * 5.2 * mm, ln)

    desc_lines = _wrap_lines(sig_desc, right_w, "Helvetica", 9.7)
    c.setFillColor(muted)
    c.setFont("Helvetica", 9.7)
    desc_y = dish_name_y - max(1, len(_wrap_lines(sig_title, right_w, "Helvetica-Bold", 12)[:2])) * 5.2 * mm - 1.6 * mm
    for i, ln in enumerate(desc_lines[:3]):
        c.drawString(right_x, desc_y - i * 4.5 * mm, ln)

    # QR kept simple: slightly smaller CTA, aligned with the right content column, and moved lower.
    qr_size = 40 * mm
    qr_x = right_x + (right_w - qr_size) / 2
    qr_y = outer + 4 * mm
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 10.2)
    cta_lines = _wrap_lines(cta, right_w, "Helvetica-Bold", 10.2)
    cta_top_y = qr_y + qr_size + 5.5 * mm
    for i, ln in enumerate(cta_lines[:2]):
        c.drawString(right_x, cta_top_y - i * 4.8 * mm, ln)
    c.drawImage(ImageReader(qr_img), qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")

    # Fine divider and simple footer info, no extra outer frame.
    footer_y = outer + 1.5 * mm
    c.setStrokeColor(line)
    c.setLineWidth(0.8)
    c.line(outer, footer_y + 22 * mm, outer + left_w - 4 * mm, footer_y + 22 * mm)

    contact = listing.get("contact") or {}
    phone = (contact.get("phone") or contact.get("whatsapp") or "").strip()
    instagram = (contact.get("instagram") or "").strip()
    if instagram.startswith('@'):
        instagram = instagram[1:]
    contact_bits = []
    if phone:
        contact_bits.append(phone)
    contact_text = " · ".join(contact_bits)

    c.setFillColor(ink)
    c.setFont("Helvetica-Bold", 10.4)
    c.drawString(outer, footer_y + 15.2 * mm, _truncate_with_ellipsis(title, left_w + 18 * mm, "Helvetica-Bold", 10.4))

    if subtitle:
        c.setFillColor(muted)
        c.setFont("Helvetica", 9.6)
        c.drawString(outer, footer_y + 10.0 * mm, _truncate_with_ellipsis(subtitle, left_w + 18 * mm, "Helvetica", 9.6))

    if contact_text:
        c.setFillColor(muted)
        c.setFont("Helvetica", 9.4)
        c.drawString(outer, footer_y + 5.2 * mm, _truncate_with_ellipsis(contact_text, left_w + 18 * mm, "Helvetica", 9.4))

    c.showPage()
    c.save()

    pdf.seek(0)
    return _pdf_stream_response(pdf, f"{listing['slug']}-promo-poster.pdf", download=download)

def _wrap_lines(text: str, max_width_pt: float, font_name: str, font_size: float) -> list[str]:
    """Simple word-wrap helper for ReportLab canvas."""
    s = (text or '').strip()
    if not s:
        return []
    words = s.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        trial = (' '.join(cur + [w])).strip()
        if cur and stringWidth(trial, font_name, font_size) > max_width_pt:
            lines.append(' '.join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(' '.join(cur))
    return lines



def _menu_poster_groups(listing: dict, lang: str = "en") -> list[dict]:
    """Build grouped menu data with section metadata for menu posters."""
    lang = (lang or "en").lower().strip()
    if lang not in ("en", "no"):
        lang = "en"
    menu = listing.get("menu") or []
    serves_order = {"single": 1, "family": 2, "group": 3}
    serves_labels = {
        "en": {"single": "Single", "family": "Family", "group": "Group"},
        "no": {"single": "En porsjon", "family": "Familie", "group": "Gruppe"},
    }
    section_presets = {
        "mains": {"en": "Mains", "no": "Hovedretter"},
        "sides": {"en": "Sides", "no": "Tilbehør"},
        "desserts": {"en": "Desserts", "no": "Dessert"},
        "drinks": {"en": "Drinks", "no": "Drikke"},
        "combos": {"en": "Combos", "no": "Kombinasjoner"},
        "specials": {"en": "Specials", "no": "Spesialiteter"},
    }
    fallback_section_label = "Other dishes" if lang == "en" else "Andre retter"

    def dish_name(dish: dict) -> str:
        if (dish.get("title") or "").strip():
            return str(dish.get("title") or "").strip()
        nm = dish.get("name")
        if isinstance(nm, dict):
            return str(nm.get(lang) or nm.get("en") or nm.get("no") or "").strip()
        return str(nm or "").strip()

    def dish_desc(dish: dict) -> str:
        ing = dish.get("ingredients")
        if isinstance(ing, str) and ing.strip():
            return ing.strip()
        desc = dish.get("desc")
        if isinstance(desc, dict):
            return str(desc.get(lang) or desc.get("en") or desc.get("no") or "").strip()
        return ""

    def _norm_key(s: str) -> str:
        s = (s or "").strip().lower()
        out = []
        last_dash = False
        for ch in s:
            if ch.isalnum():
                out.append(ch)
                last_dash = False
            else:
                if not last_dash:
                    out.append("-")
                    last_dash = True
        k = "".join(out).strip("-")
        return k or "dish"

    def _dish_key(dish: dict) -> str:
        dk = (dish.get("dish_key") or "").strip()
        if dk:
            return _norm_key(dk)
        return _norm_key(dish_name(dish) or "")

    def _section_meta(dish: dict) -> dict:
        custom = str(dish.get("menu_section_custom") or "").strip()
        if custom:
            return {"id": f"custom:{custom.lower()}", "label": custom, "is_fallback": False}
        key = str(dish.get("menu_section_key") or "").strip().lower()
        if key:
            preset = section_presets.get(key) or {}
            return {"id": f"preset:{key}", "label": str(preset.get(lang) or preset.get("en") or key).strip(), "is_fallback": False}
        return {"id": "uncategorized", "label": fallback_section_label, "is_fallback": True}

    def _dish_image_path(dish: dict):
        slug = str(listing.get("slug") or "").strip().lower()
        title_l = dish_name(dish).lower()
        img_raw = str(dish.get("image") or "")
        if slug == "marias-filipino-kusina":
            if "adobo" in title_l:
                forced = _resolve_public_image_path("assets/dish_adobo_custom.png")
                if forced is not None:
                    return forced
            if ("lumpia" in title_l) or ("vårr" in title_l) or ("värr" in title_l):
                forced = _resolve_public_image_path("assets/dish_lumpia_custom.png")
                if forced is not None:
                    return forced
            if "barkada" in title_l:
                forced = _resolve_public_image_path("assets/dish_barkada_custom.png")
                if forced is not None:
                    return forced
            if "dish_lumpia" in img_raw:
                forced = _resolve_public_image_path("assets/dish_lumpia_custom.png")
                if forced is not None:
                    return forced
            if ("dish_family3" in img_raw) or ("dish_barkada" in img_raw):
                forced = _resolve_public_image_path("assets/dish_barkada_custom.png")
                if forced is not None:
                    return forced
        p = _resolve_public_image_path(img_raw)
        if p is not None:
            return p
        return _resolve_public_image_path(str(listing.get("hero_image") or ""))

    groups_map: dict[str, dict] = {}
    for idx, it in enumerate(menu):
        if not isinstance(it, dict):
            continue
        nm = dish_name(it)
        if not nm:
            continue
        key = _dish_key(it)
        g = groups_map.get(key)
        if not g:
            g = {"key": key, "title": nm, "items": [], "desc_source": None, "first_index": idx}
            groups_map[key] = g
        if (it.get("serves") == "single") and nm:
            g["title"] = nm
        if g.get("desc_source") is None and dish_desc(it):
            g["desc_source"] = it
        g["items"].append(it)

    groups: list[dict] = []
    for g in groups_map.values():
        entries = g.get("items") or []
        rep = next((x for x in entries if x.get("serves") == "single"), None) or (entries[0] if entries else {})
        opts = []
        for it in entries:
            serves = (it.get("serves") or "").lower().strip()
            label = serves_labels.get(lang, serves_labels["en"]).get(serves, serves.title() if serves else ("Option" if lang == "en" else "Valg"))
            note = ""
            n = it.get("note")
            if isinstance(n, dict):
                note = str(n.get(lang) or n.get("en") or n.get("no") or "").strip()
            elif isinstance(n, str):
                note = n.strip()
            if note:
                label = f"{label} — {note}"[:70]
            opts.append({
                "kind": "serves",
                "order": serves_order.get(serves, 9),
                "label": label,
                "price": it.get("price"),
                "sold_out": bool(it.get("sold_out")),
            })
            variants = it.get("variants")
            if isinstance(variants, list) and variants:
                for v in variants[:8]:
                    if not isinstance(v, dict):
                        continue
                    vn = str(v.get("name") or "").strip()
                    vp = v.get("price")
                    if not vn and vp is None:
                        continue
                    opts.append({
                        "kind": "variant",
                        "order": 20,
                        "label": vn[:70] or ("Variant" if lang == "en" else "Variant"),
                        "price": vp,
                        "sold_out": False,
                    })
        seen = set()
        dedup = []
        for o in sorted(opts, key=lambda x: (x.get("order", 99), x.get("label", ""))):
            k = (o.get("label") or "").strip().lower() + "|" + str(o.get("price") or "")
            if k in seen:
                continue
            seen.add(k)
            dedup.append(o)
        prices = [o.get("price") for o in dedup if o.get("price") is not None]
        try:
            from_price = min([float(p) for p in prices]) if prices else 0
        except Exception:
            from_price = 0
        sec = _section_meta(rep)
        ingredients_val = rep.get("ingredients")
        ingredients_list = []
        if isinstance(ingredients_val, dict):
            raw_ing = ingredients_val.get(lang) or ingredients_val.get("en") or ingredients_val.get("no") or []
            if isinstance(raw_ing, list):
                ingredients_list = [str(x).strip() for x in raw_ing if str(x).strip()][:8]
            elif isinstance(raw_ing, str) and raw_ing.strip():
                ingredients_list = [s.strip() for s in raw_ing.split(",") if s.strip()][:8]
        elif isinstance(ingredients_val, list):
            ingredients_list = [str(x).strip() for x in ingredients_val if str(x).strip()][:8]
        elif isinstance(ingredients_val, str) and ingredients_val.strip():
            ingredients_list = [s.strip() for s in ingredients_val.split(",") if s.strip()][:8]

        groups.append({
            "key": g.get("key"),
            "title": g.get("title"),
            "options": dedup,
            "from_price": from_price,
            "desc": dish_desc(g.get("desc_source") or {}) if g.get("desc_source") else "",
            "ingredients": ingredients_list,
            "first_index": g.get("first_index", 0),
            "section_id": sec.get("id"),
            "section_label": sec.get("label"),
            "section_fallback": bool(sec.get("is_fallback")),
            "image_path": _dish_image_path(rep),
            "image_focal_x": max(0.0, min(100.0, float(rep.get("image_focal_x") or 50))),
            "image_focal_y": max(0.0, min(100.0, float(rep.get("image_focal_y") or 50))),
            "image_zoom": max(100.0, min(200.0, float(rep.get("image_zoom") or 120))),
        })

    groups.sort(key=lambda x: x.get("first_index", 0))
    explicit_count = len({g.get("section_id") for g in groups if not g.get("section_fallback")})
    should_show_sections = explicit_count > 0 or len({g.get("section_id") for g in groups}) > 1
    sections = []
    sec_map: dict[str, dict] = {}
    for g in groups:
        sid = g.get("section_id") if should_show_sections else "__all"
        if sid not in sec_map:
            sec_map[sid] = {"id": sid, "label": g.get("section_label") if should_show_sections else "", "items": []}
            sections.append(sec_map[sid])
        sec_map[sid]["items"].append(g)
    return sections


def _make_menu_poster_pdf(listing: dict, request: Request, lang: str = "en", size: str = "a4", style: str = "text", name_color: str = "", section_color: str = "", body_color: str = "", frame_color: str = "", max_dishes: int = 0, hero_focal_x: float = 50.0, hero_focal_y: float = 50.0, hero_zoom: float = 100.0, styled_bg_color: str = "", styled_card_color: str = "", styled_name_color: str = "", styled_section_color: str = "", styled_body_color: str = "", styled_desc_color: str = "", styled_line_color: str = "", styled_columns: int = 1, styled_flow: str = "column") -> BytesIO:
    """Menu poster PDFs in three styles: text, hero, and visual."""
    lang = (lang or "en").lower().strip()
    if lang not in ("en", "no"):
        lang = "en"
    size = (size or "a4").lower().strip()
    pagesize = A4 if size == "a4" else A3
    W, H = pagesize
    style = (style or "text").lower().strip()
    if style not in ("text", "hero", "visual", "styled", "styled_text", "styled_grid", "grid", "sections"):
        style = "hero" if style in ("photo", "image") else "text"

    margin = 14 * mm
    url = _public_listing_url(request, listing.get("slug") or "")
    currency = listing.get("currency") or ""
    title = listing.get("name") or "Kitchen"
    subtitle = f"{listing.get('area','')} · {listing.get('city','')}".strip(" ·")
    sections = _menu_poster_groups(listing, lang=lang)
    groups = [g for sec in sections for g in (sec.get("items") or [])]
    try:
        max_dishes = int(max_dishes or 0)
    except Exception:
        max_dishes = 0
    if max_dishes > 0 and len(groups) > max_dishes:
        remaining = max_dishes
        limited_sections = []
        for sec in sections:
            items = list(sec.get("items") or [])
            if remaining <= 0:
                break
            if len(items) <= remaining:
                limited_sections.append({**sec, "items": items})
                remaining -= len(items)
            else:
                limited_sections.append({**sec, "items": items[:remaining]})
                remaining = 0
                break
        sections = [sec for sec in limited_sections if (sec.get("items") or [])]
        groups = [g for sec in sections for g in (sec.get("items") or [])]

    avail = listing.get("availability") or {}
    a = (avail.get(lang) if isinstance(avail, dict) else {}) or {}
    deadline = (a.get("deadline") or "").strip()
    window = (a.get("window") or "").strip()
    contact = listing.get("contact") or {}

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = None

    try:
        hero_focal_x = max(0.0, min(100.0, float(hero_focal_x or 50.0)))
    except Exception:
        hero_focal_x = 50.0
    try:
        hero_focal_y = max(0.0, min(100.0, float(hero_focal_y or 50.0)))
    except Exception:
        hero_focal_y = 50.0
    try:
        hero_zoom = max(100.0, min(200.0, float(hero_zoom or 100.0)))
    except Exception:
        hero_zoom = 100.0
    try:
        styled_columns = int(styled_columns or 1)
    except Exception:
        styled_columns = 1
    styled_columns = 2 if styled_columns == 2 else 1
    _styled_flow_raw = str(styled_flow or '').lower()
    if _styled_flow_raw == 'row':
        styled_flow = 'row'
    elif _styled_flow_raw == 'fill':
        styled_flow = 'fill'
    else:
        styled_flow = 'column'

    hero_reader = None
    hero_h = 38 * mm if size == "a4" else 54 * mm
    if style in ("hero", "visual"):
        hero_path = _resolve_public_image_path(str(listing.get("hero_image") or ""))
        if hero_path is not None:
            try:
                img = Image.open(hero_path)
                img2 = _cover_crop_adjusted(img, max(640, int(W - 2 * margin)), max(240, int(hero_h)), focal_x=hero_focal_x, focal_y=hero_focal_y, zoom=hero_zoom)
                hero_reader = ImageReader(img2)
            except Exception:
                hero_reader = None

    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=pagesize)

    def _poster_hex(value: str, fallback: str) -> str:
        try:
            return _rgb01_to_hex(_hex_to_rgb01(str(value or fallback), _hex_to_rgb01(fallback)), fallback)
        except Exception:
            return fallback

    name_hex = _poster_hex(name_color, "#16181d")
    section_hex = _poster_hex(section_color, "#946b29")
    body_hex = _poster_hex(body_color, "#1f2329")
    frame_hex = _poster_hex(frame_color, "#d7d0c5")
    muted_hex = _rgb01_to_hex(tuple(max(0.0, min(1.0, v * 0.74 + 0.18)) for v in _hex_to_rgb01(body_hex, (0.12, 0.14, 0.16))), "#62676f")
    light_line_hex = _rgb01_to_hex(tuple(max(0.0, min(1.0, v * 0.18 + 0.82)) for v in _hex_to_rgb01(frame_hex, (0.84, 0.82, 0.78))), "#d7d0c5")

    NAME_COLOR = colors.HexColor(name_hex)
    SECTION_COLOR = colors.HexColor(section_hex)
    BODY_COLOR = colors.HexColor(body_hex)
    MUTED_COLOR = colors.HexColor(muted_hex)
    FRAME_COLOR = colors.HexColor(frame_hex)
    LIGHT_LINE_COLOR = colors.HexColor(light_line_hex)

    qr_img = qr.make_image(fill_color=body_hex, back_color="#ffffff").convert("RGB")

    def draw_common_header(y_top: float, include_divider: bool = True, title_font_delta: int = 0, gap_above_title: float = 10, subtitle_gap: float = 20):
        title_size = (22 if size == "a4" else 28) + int(title_font_delta or 0)
        subtitle_size = 11 if size == "a4" else 12
        c.setFillColor(NAME_COLOR)
        c.setFont("Helvetica-Bold", title_size)
        c.drawString(margin, y_top - gap_above_title, title)
        yy = y_top - gap_above_title - subtitle_gap
        if subtitle:
            c.setFillColor(MUTED_COLOR)
            c.setFont("Helvetica", subtitle_size)
            c.drawString(margin, yy, subtitle)
            yy -= 15
        # Keep the menu posters cleaner: no pickup/deadline meta line under the subtitle.
        if include_divider:
            c.setStrokeColor(LIGHT_LINE_COLOR)
            c.setLineWidth(1)
            c.line(margin, yy - 2, W - margin, yy - 2)
            yy -= 8
        return yy

    def draw_footer(show_label: str = None, *, inside_frame: bool = False, frame_left: float | None = None, frame_right: float | None = None, frame_bottom: float | None = None):
        qr_size = 24 * mm if size == "a4" else 30 * mm
        if inside_frame and frame_left is not None and frame_right is not None and frame_bottom is not None:
            left = frame_left + 6 * mm
            right = frame_right - 6 * mm
            bottom = frame_bottom + 3.5 * mm
            heading = show_label or ("Contact" if lang == "en" else "Kontakt")
            lines = []
            if contact.get("phone"):
                lines.append(("Phone" if lang == "en" else "Telefon") + f": {contact.get('phone')}")
            elif contact.get("whatsapp"):
                lines.append(("WhatsApp" if lang == "en" else "WhatsApp") + f": {contact.get('whatsapp')}")
            if contact.get("instagram"):
                lines.append(f"Instagram: @{contact.get('instagram')}")
            if contact.get("email"):
                lines.append(f"Email: {contact.get('email')}")
            line_gap = 10
            body_lines = min(3, len(lines))
            block_height = 12 + (line_gap * body_lines)
            qr_size = min(block_height + 2, 20 * mm if size == "a4" else 24 * mm)
            qr_x = right - qr_size
            qr_y = bottom + 0.5 * mm
            c.drawImage(ImageReader(qr_img), qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")
            top_y = bottom + block_height
            c.setFillColor(BODY_COLOR)
            c.setFont("Helvetica-Bold", 13)
            c.drawString(left, top_y, heading)
            c.setFillColor(MUTED_COLOR)
            c.setFont("Helvetica", 9)
            y0 = top_y - 10
            for ln in lines[:3]:
                c.drawString(left, y0, ln[:100])
                y0 -= line_gap
            return
        qr_x = W - margin - qr_size
        qr_y = margin + 8 * mm
        c.drawImage(ImageReader(qr_img), qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")
        c.setFillColor(BODY_COLOR)
        c.setFont("Helvetica-Bold", 13)
        heading = show_label or ("Menu" if lang == "en" else "Meny")
        if currency and heading in (("Menu" if lang == "en" else "Meny"), ("Full menu" if lang == "en" else "Full meny")):
            heading = f"{heading}  ({currency})"
        c.drawString(margin, margin + 22 * mm, heading)
        c.setFillColor(MUTED_COLOR)
        c.setFont("Helvetica", 9)
        y0 = margin + 16 * mm
        lines = []
        if contact.get("phone"):
            lines.append(("Phone" if lang == "en" else "Telefon") + f": {contact.get('phone')}")
        elif contact.get("whatsapp"):
            lines.append(("WhatsApp" if lang == "en" else "WhatsApp") + f": {contact.get('whatsapp')}")
        if contact.get("instagram"):
            lines.append(f"Instagram: @{contact.get('instagram')}")
        if contact.get("email"):
            lines.append(f"Email: {contact.get('email')}")
        for ln in lines[:3]:
            c.drawString(margin, y0, ln[:100])
            y0 -= 10

    def fmt_price(p, prefix_from=False):
        if p is None or p == "":
            return ""
        try:
            val = int(float(p))
        except Exception:
            return str(p)
        if prefix_from:
            prefix = "From" if lang == "en" else "Fra"
            return f"{prefix} {val} {currency}" if currency else f"{prefix} {val}"
        return f"{val} {currency}" if currency else f"{val}"

    if style in ("text", "hero"):
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        y_top = H - margin
        if style == "hero" and hero_reader is not None:
            img_x = margin
            img_y = y_top - hero_h
            img_w = W - 2 * margin
            hero_radius = 3 * mm
            pth = c.beginPath()
            pth.roundRect(img_x, img_y, img_w, hero_h, hero_radius)
            c.saveState()
            c.clipPath(pth, stroke=0, fill=0)
            c.drawImage(hero_reader, img_x, img_y, width=img_w, height=hero_h, mask="auto")
            c.restoreState()
            c.setStrokeColor(FRAME_COLOR)
            c.setLineWidth(0.8)
            c.roundRect(img_x, img_y, img_w, hero_h, hero_radius, stroke=1, fill=0)
            y_top = img_y - 11
        if style == "hero":
            header_bottom = draw_common_header(y_top, include_divider=False, title_font_delta=-2, gap_above_title=14, subtitle_gap=22)
        else:
            header_bottom = draw_common_header(y_top, include_divider=(style != "text"))
        footer_h = 34 * mm
        frame_top_gap = (2.5 * mm if style == "hero" else 4 * mm)
        frame_bottom_gap = 3 * mm
        content_top = header_bottom - 12
        frame_bottom = margin + frame_bottom_gap
        content_bottom = frame_bottom + footer_h
        frame_top = header_bottom - frame_top_gap
        dish_count = len(groups)
        section_count = len([sec for sec in sections if (sec.get("items") or [])])
        if size == "a3":
            cols = 3 if dish_count >= 18 else 2
        else:
            cols = 3 if dish_count >= 22 else (2 if dish_count >= 10 else 1)
        gap = 8 * mm if cols >= 3 else 10 * mm
        frame_left = margin
        frame_right = W - margin
        frame_w = frame_right - frame_left
        c.setStrokeColor(FRAME_COLOR)
        c.setLineWidth(1.0)
        c.roundRect(frame_left, frame_bottom, frame_w, max(24 * mm, frame_top - frame_bottom), 3.5 * mm, stroke=1, fill=0)
        inner_pad_x = 6 * mm
        inner_pad_top = 7 * mm
        inner_pad_bottom = 6 * mm
        content_left = frame_left + inner_pad_x
        content_right = frame_right - inner_pad_x
        available_w = content_right - content_left
        col_w = (available_w - gap * (cols - 1)) / cols
        y = frame_top - inner_pad_top
        col = 0
        x0 = content_left

        def next_col_or_page():
            nonlocal col, x0, y
            if col + 1 < cols:
                col += 1
                x0 = content_left + col * (col_w + gap)
                y = frame_top - inner_pad_top
                return
            c.showPage()
            c.setFillColorRGB(1, 1, 1)
            c.rect(0, 0, W, H, stroke=0, fill=1)
            new_y_top = H - margin
            if style == "hero" and hero_reader is not None:
                img_x = margin
                img_y = new_y_top - hero_h
                img_w = W - 2 * margin
                hero_radius = 3 * mm
                pth = c.beginPath()
                pth.roundRect(img_x, img_y, img_w, hero_h, hero_radius)
                c.saveState()
                c.clipPath(pth, stroke=0, fill=0)
                c.drawImage(hero_reader, img_x, img_y, width=img_w, height=hero_h, mask="auto")
                c.restoreState()
                c.setStrokeColor(FRAME_COLOR)
                c.setLineWidth(0.8)
                c.roundRect(img_x, img_y, img_w, hero_h, hero_radius, stroke=1, fill=0)
                new_y_top = img_y - 12
            draw_common_header(new_y_top)
            c.setStrokeColor(FRAME_COLOR)
            c.setLineWidth(1.0)
            c.roundRect(frame_left, frame_bottom, frame_w, max(24 * mm, frame_top - frame_bottom), 3.5 * mm, stroke=1, fill=0)
            col = 0
            x0 = content_left
            y = frame_top - inner_pad_top

        def ensure_space(need: float):
            nonlocal y
            if y - need < content_bottom:
                next_col_or_page()

        first_section = True
        for sec in sections:
            sec_label = str(sec.get("label") or "").strip()
            if sec_label:
                if not first_section:
                    ensure_space(10)
                    y -= 8
                ensure_space(28)
                c.setFillColor(SECTION_COLOR)
                c.setFont("Helvetica-Bold", 10 if size == "a4" else 12)
                c.drawString(x0 + 2 * mm, y + 1, sec_label.upper()[:28])
                c.setStrokeColor(SECTION_COLOR)
                c.setLineWidth(0.8)
                c.line(x0, y - 5, x0 + col_w, y - 5)
                y -= 20
                first_section = False
            for g in sec.get("items") or []:
                nm = str(g.get("title") or "").strip() or ("Untitled" if lang == "en" else "Uten navn")
                opts = g.get("options") or []
                all_sold = bool(opts) and all(bool(o.get("sold_out")) for o in opts if o.get("kind") == "serves")
                ensure_space(18)
                c.setFillColor(BODY_COLOR)
                c.setFont("Helvetica-Bold", 8)
                name_line = nm + ("  (Sold out)" if (all_sold and lang == "en") else ("  (Utsolgt)" if all_sold else ""))
                name_lines = _wrap_lines(name_line, col_w - 52, "Helvetica-Bold", 8) or [name_line]
                c.drawString(x0, y, name_lines[0])
                price_txt = ""
                priced = [o for o in opts if o.get("price") is not None]
                if len(priced) == 1:
                    price_txt = fmt_price(priced[0].get("price"))
                elif priced:
                    price_txt = fmt_price(g.get("from_price"), prefix_from=True)
                if price_txt:
                    c.setFont("Helvetica-Bold", 8)
                    c.drawRightString(x0 + col_w, y, price_txt)
                y -= 12
                if len(name_lines) > 1:
                    c.setFillColor(MUTED_COLOR)
                    c.setFont("Helvetica", 8)
                    for extra in name_lines[1:3]:
                        ensure_space(12)
                        c.drawString(x0, y, extra)
                        y -= 11
                if opts:
                    c.setFillColor(MUTED_COLOR)
                    c.setFont("Helvetica", 8)
                    for o in opts[:10]:
                        label = str(o.get("label") or "").strip()
                        p_txt = fmt_price(o.get("price")) if o.get("price") is not None else ""
                        if o.get("sold_out"):
                            label += " (Sold out)" if lang == "en" else " (Utsolgt)"
                        ensure_space(12)
                        c.drawString(x0 + 10, y, f"• {label}"[:70])
                        if p_txt:
                            c.drawRightString(x0 + col_w, y, p_txt)
                        y -= 11
                desc = (g.get("desc") or "").strip()
                if desc:
                    c.setFillColor(MUTED_COLOR)
                    c.setFont("Helvetica", 8)
                    for ln in _wrap_lines(desc, col_w - 6, "Helvetica", 9)[:3]:
                        ensure_space(12)
                        c.drawString(x0 + 6, y, ln)
                        y -= 11
                y -= 6
        draw_footer("Contact" if lang == "en" else "Kontakt", inside_frame=True, frame_left=frame_left, frame_right=frame_right, frame_bottom=frame_bottom)
        c.showPage()
        c.save()
        pdf.seek(0)
        return pdf

    if style in ("styled", "styled_text", "styled_grid"):
        is_styled_text = (style == "styled_text")
        is_styled_grid = (style == "styled_grid")
        styled_bg_hex = _poster_hex(styled_bg_color, "#efe8dc")
        styled_card_hex = _poster_hex(styled_card_color, "#efe8dc")
        styled_name_hex = _poster_hex(styled_name_color, "#40342a")
        styled_section_hex = _poster_hex(styled_section_color, "#7b6854")
        styled_body_hex = _poster_hex(styled_body_color, "#736659")
        styled_desc_hex = _poster_hex(styled_desc_color, "#8e7f71")
        styled_line_hex = _poster_hex(styled_line_color, "#d8c5b2")
        styled_soft_hex = _rgb01_to_hex(tuple(max(0.0, min(1.0, v * 0.92 + 0.03)) for v in _hex_to_rgb01(styled_card_hex, (0.95, 0.91, 0.85))), "#e8dece")
        BG_COLOR = colors.HexColor(styled_bg_hex)
        CARD_FILL = colors.HexColor(styled_card_hex)
        SOFT_FILL = colors.HexColor(styled_soft_hex)
        LINE_COLOR = colors.HexColor(styled_line_hex)
        PRICE_COLOR = colors.HexColor(styled_body_hex)
        PRICE_FONT = "Helvetica"
        c.setFillColor(BG_COLOR)
        c.rect(0, 0, W, H, stroke=0, fill=1)

        page_pad_x = 16 * mm if size == "a4" else 20 * mm
        page_pad_top = 11 * mm if size == "a4" else 14 * mm
        page_pad_bottom = 14 * mm if size == "a4" else 18 * mm
        footer_h = 26 * mm if size == "a4" else 32 * mm
        content_left = page_pad_x
        content_right = W - page_pad_x
        content_w = content_right - content_left
        max_content_w = (182 * mm if size == "a4" else 230 * mm) if is_styled_grid else (156 * mm if size == "a4" else 205 * mm)
        if content_w > max_content_w:
            extra = (content_w - max_content_w) / 2.0
            content_left += extra
            content_right -= extra
            content_w = max_content_w

        kitchen_name_size = 18 if size == "a4" else 23
        title_size = 12 if size == "a4" else 15
        section_size = 10 if size == "a4" else 12
        name_size = 9.4 if size == "a4" else 11.0
        desc_size = 7.6 if size == "a4" else 8.8
        price_size = 9.4 if size == "a4" else 11.0
        thumb_w = (18 * mm if size == "a4" else 24 * mm) if is_styled_grid else (23 * mm if size == "a4" else 30 * mm)
        row_min_h = (9.8 * mm if size == "a4" else 12.4 * mm) if is_styled_text else ((27.5 * mm if size == "a4" else 34.0 * mm) if is_styled_grid else (14.5 * mm if size == "a4" else 18.5 * mm))
        row_gap = (2.6 * mm if size == "a4" else 3.4 * mm) if is_styled_text else ((4.2 * mm if size == "a4" else 5.2 * mm) if is_styled_grid else (4.8 * mm if size == "a4" else 6.0 * mm))
        sec_gap = (7.4 * mm if size == "a4" else 9.2 * mm) if is_styled_text else ((7.0 * mm if size == "a4" else 8.5 * mm) if is_styled_grid else (10.0 * mm if size == "a4" else 12.0 * mm))
        header_h = (35 * mm if size == "a4" else 43 * mm) if is_styled_grid else (30 * mm if size == "a4" else 37 * mm)
        section_header_h = 8 * mm if size == "a4" else 9 * mm
        content_top_start = H - page_pad_top - header_h
        content_bottom = page_pad_bottom + footer_h

        def _draw_tracked_text(x, y, text, font_name, font_size, tracking=0.0, centered=False, color=None):
            txt = str(text or "")
            if not txt:
                return 0.0
            if color is not None:
                c.setFillColor(color)
            c.setFont(font_name, font_size)
            total_w = c.stringWidth(txt, font_name, font_size) + max(0, len(txt) - 1) * tracking
            cur_x = x - (total_w / 2.0 if centered else 0.0)
            for idx, ch in enumerate(txt):
                c.drawString(cur_x, y, ch)
                cur_x += c.stringWidth(ch, font_name, font_size)
                if idx < len(txt) - 1:
                    cur_x += tracking
            return total_w

        def draw_page_shell(page_no: int):
            header_top = H - page_pad_top
            center_x = (content_left + content_right) / 2.0
            kitchen_label = str(title or "Kitchen")[:44]
            kitchen_fs = 20 if size == "a4" else 25
            menu_fs = 8.6 if size == "a4" else 10.0
            header_drop = (4.0 * mm if size == "a4" else 5.0 * mm) if is_styled_grid else 2.2 * mm
            ornament_y = header_top - 10.4 * mm - header_drop
            menu_y = ornament_y - 4.8 * mm
            name_y = menu_y + 8.4 * mm

            # Premium print-style heading: elegant kitchen name, restrained MENU label,
            # and a small ornamental divider, while keeping the actual menu area web-like.
            c.setFillColor(colors.HexColor(styled_name_hex))
            c.setFont("Times-Italic", kitchen_fs)
            c.drawCentredString(center_x, name_y, kitchen_label)

            menu_word = "MENU" if lang == "en" else "MENY"
            _draw_tracked_text(center_x, menu_y, menu_word, "Helvetica", menu_fs, tracking=1.35, centered=True, color=colors.HexColor(styled_section_hex))

            c.setStrokeColor(colors.HexColor(styled_line_hex))
            c.setLineWidth(0.8)
            ornament_gap = 8 * mm
            ornament_half = 1.15 * mm
            left_start = max(content_left + 8 * mm, center_x - 36 * mm)
            left_end = center_x - ornament_gap
            right_start = center_x + ornament_gap
            right_end = min(content_right - 8 * mm, center_x + 36 * mm)
            if left_end - left_start > 6 * mm:
                c.line(left_start, ornament_y, left_end, ornament_y)
            if right_end - right_start > 6 * mm:
                c.line(right_start, ornament_y, right_end, ornament_y)
            diamond = c.beginPath()
            diamond.moveTo(center_x, ornament_y + ornament_half)
            diamond.lineTo(center_x + ornament_half, ornament_y)
            diamond.lineTo(center_x, ornament_y - ornament_half)
            diamond.lineTo(center_x - ornament_half, ornament_y)
            diamond.close()
            c.setFillColor(colors.HexColor(styled_section_hex))
            c.drawPath(diamond, stroke=0, fill=1)

            if page_no > 1:
                c.setFillColor(MUTED_COLOR)
                c.setFont("Helvetica", 8)
                c.drawRightString(content_right, header_top - 1.2 * mm, f"Page {page_no}")
            return content_top_start

        def draw_styled_footer(page_no: int, total_pages: int):
            footer_y = page_pad_bottom
            line_y = footer_y + footer_h - 1.5 * mm
            c.setStrokeColor(LINE_COLOR)
            c.setLineWidth(0.8)
            c.line(content_left, line_y, content_right, line_y)

            qr_bg_hex = styled_bg_hex
            qr_fg_hex = styled_section_hex
            qr_local = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=1)
            qr_local.add_data(url)
            qr_local.make(fit=True)
            qr_local_img = qr_local.make_image(fill_color=qr_fg_hex, back_color=qr_bg_hex).convert("RGB")
            qr_size = 15.8 * mm if size == "a4" else 18.8 * mm
            qr_x = content_right - qr_size
            qr_y = footer_y + 5.4 * mm

            footer_left = content_left
            footer_right = qr_x - 6 * mm
            visit_words = ("VISIT OUR KITCHEN" if lang == "en" else "BESØK KJØKKENET VÅRT").split()
            label_y = footer_y + footer_h - 10.3 * mm
            visit_font = 8.6 if size == "a4" else 9.8
            visit_gap = 3.55 * mm if size == "a4" else 4.1 * mm
            visit_x = qr_x - 18.6 * mm
            for i, word in enumerate(visit_words[:3]):
                _draw_tracked_text(
                    visit_x,
                    label_y - i * visit_gap,
                    word,
                    "Helvetica",
                    visit_font,
                    tracking=0.7,
                    centered=False,
                    color=colors.HexColor(styled_section_hex),
                )
            c.drawImage(ImageReader(qr_local_img), qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")
            contact_lines = []
            phone = str(contact.get("phone") or "").strip()
            whatsapp = str(contact.get("whatsapp") or "").strip()
            instagram = str(contact.get("instagram") or "").strip()
            email = str(contact.get("email") or "").strip()
            website = str(url or "").replace("https://", "").replace("http://", "")
            if phone:
                contact_lines.append(phone)
            elif whatsapp:
                contact_lines.append(f"WhatsApp: {whatsapp}")
            if instagram:
                contact_lines.append(f"@{instagram}")
            if email:
                contact_lines.append(email)
            if website:
                contact_lines.append(website)
            contact_lines = contact_lines[:3]

            label = "CONTACT" if lang == "en" else "KONTAKT"
            _draw_tracked_text(footer_left, footer_y + footer_h - 6.2 * mm, label, "Helvetica", 8.6 if size == "a4" else 9.8, tracking=0.7, centered=False, color=colors.HexColor(styled_section_hex))
            c.setFillColor(colors.HexColor(styled_body_hex))
            c.setFont("Times-Italic", 8.4 if size == "a4" else 9.5)
            ty = footer_y + footer_h - 10.6 * mm
            max_w = max(35 * mm, footer_right - footer_left)
            for line in contact_lines:
                wrapped = _wrap_lines(str(line), max_w, "Times-Italic", 8.4 if size == "a4" else 9.5)[:1]
                for ln in wrapped:
                    c.drawString(footer_left, ty, ln)
                    ty -= 4.0 * mm

            if total_pages > 1:
                c.setFillColor(MUTED_COLOR)
                c.setFont("Helvetica", 7.8 if size == "a4" else 8.6)
                c.drawRightString(footer_right, footer_y + 2.8 * mm, f"{page_no}/{total_pages}")

        def draw_thumb(path, x, yb, w, h, focal_x=50.0, focal_y=50.0, zoom=120.0):
            pth = c.beginPath()
            pth.roundRect(x, yb, w, h, 4.0 * mm)
            c.saveState()
            c.clipPath(pth, stroke=0, fill=0)
            drawn = False
            if path is not None:
                try:
                    img = Image.open(path)
                    img2 = _cover_crop_adjusted(img, max(260, int(w)), max(180, int(h)), focal_x, focal_y, zoom)
                    c.drawImage(ImageReader(img2), x, yb, width=w, height=h, mask="auto")
                    drawn = True
                except Exception:
                    drawn = False
            if not drawn:
                c.setFillColor(SOFT_FILL)
                c.rect(x, yb, w, h, stroke=0, fill=1)
            c.restoreState()

        def group_price_text(g):
            opts = [o for o in (g.get("options") or []) if o.get("price") is not None]
            if len(opts) == 1:
                return fmt_price(opts[0].get("price"), prefix_from=False)
            if g.get("from_price") is not None:
                return fmt_price(g.get("from_price"), prefix_from=False)
            return ""

        def estimate_group_h(g):
            text_w = content_w - thumb_w - 14 * mm - 18 * mm
            title_lines = _wrap_lines(str(g.get("title") or ""), text_w, "Helvetica-Bold", name_size)[:2] or [""]
            desc_lines = _wrap_lines(str(g.get("desc") or ""), text_w, "Helvetica", desc_size)[:2]
            line_h1 = 3.9 * mm
            line_h2 = 3.3 * mm
            text_h = (len(title_lines) * line_h1) + (len(desc_lines) * line_h2)
            return max(row_min_h, text_h + 4.8 * mm)

        def estimate_group_h_text(g, col_w):
            title_lines = _wrap_lines(str(g.get("title") or ""), col_w - 18 * mm, "Helvetica-Bold", name_size)[:2] or [""]
            desc_lines = _wrap_lines(str(g.get("desc") or ""), col_w - 2 * mm, "Times-Italic", desc_size)[:2]
            opts = g.get("options") or []
            option_count = min(8, len(opts))
            line_h1 = 3.9 * mm
            line_h2 = 3.25 * mm
            option_h = option_count * 3.5 * mm
            text_h = (len(title_lines) * line_h1) + (len(desc_lines) * line_h2) + option_h
            return max(row_min_h, text_h + 3.4 * mm)

        pages = []
        available_h = content_top_start - content_bottom
        sec_list = [sec for sec in sections if (sec.get("items") or [])]
        text_cols = styled_columns if is_styled_text else 1
        text_gap = 11 * mm if size == "a4" else 13 * mm
        text_col_w = (content_w - (text_gap * (text_cols - 1))) / max(1, text_cols)

        def _text_item_height(item):
            kind, obj = item
            if kind.startswith("section"):
                return section_header_h
            if kind == "group":
                return estimate_group_h_text(obj, text_col_w) + row_gap
            return 0.0

        def _split_single_section_items(label, groups):
            if len(groups) <= 1:
                return [("section", {"label": label})] + [("group", g) for g in groups], []
            total_groups_h = sum(estimate_group_h_text(g, text_col_w) + row_gap for g in groups)
            target = total_groups_h / 2.0
            left_groups = []
            used = 0.0
            remaining = list(groups)
            while len(remaining) > 1 and (not left_groups or used < target):
                g = remaining.pop(0)
                left_groups.append(g)
                used += estimate_group_h_text(g, text_col_w) + row_gap
            if not remaining:
                remaining = left_groups[-1:]
                left_groups = left_groups[:-1] or left_groups
            left_items = [("section", {"label": label})] + [("group", g) for g in left_groups]
            right_items = []
            if remaining:
                right_items.append(("section-continued", {"label": label, "continued": True}))
                right_items.extend(("group", g) for g in remaining)
            return left_items, right_items

        def _rebalance_two_col_page(page_cols):
            if text_cols != 2:
                return page_cols
            all_items = []
            for col in page_cols:
                all_items.extend(col)
            if not all_items:
                return page_cols
            col_heights = [sum(_text_item_height(it) for it in col) for col in page_cols]
            if page_cols[1] and col_heights[0] <= (col_heights[1] * 1.35 + 8 * mm):
                return page_cols
            sections_pack = []
            current = None
            for kind, obj in all_items:
                if kind.startswith("section"):
                    if current:
                        sections_pack.append(current)
                    current = {"label": obj.get("label"), "continued": (kind == "section-continued"), "groups": []}
                elif kind == "group":
                    if current is None:
                        current = {"label": "", "continued": False, "groups": []}
                    current["groups"].append(obj)
            if current:
                sections_pack.append(current)
            if not sections_pack:
                return page_cols
            if len(sections_pack) == 1:
                left, right = _split_single_section_items(sections_pack[0]["label"], sections_pack[0]["groups"])
                return [left, right]
            total_h = 0.0
            packed = []
            for sec in sections_pack:
                sec_items = [(("section-continued" if sec.get("continued") else "section"), {"label": sec.get("label"), "continued": sec.get("continued")})]
                sec_items.extend(("group", g) for g in sec.get("groups") or [])
                sec_h = sum(_text_item_height(it) for it in sec_items) + sec_gap
                packed.append((sec_items, sec_h))
                total_h += sec_h
            target = total_h / 2.0
            left, right = [], []
            left_h = 0.0
            for idx, (sec_items, sec_h) in enumerate(packed):
                remaining = len(packed) - idx
                if not right and left and (left_h >= target or remaining == 1):
                    right.extend(sec_items)
                elif left_h + sec_h <= target * 1.12 or not left:
                    left.extend(sec_items)
                    left_h += sec_h
                else:
                    right.extend(sec_items)
            if not right and left:
                moved = packed[-1][0]
                moved_len = len(moved)
                right = left[-moved_len:]
                left = left[:-moved_len]
            return [left, right]

        if is_styled_text:
            cur_page = [[] for _ in range(text_cols)]
            cur_col = 0
            cur_used = [0.0 for _ in range(text_cols)]
            for sec in sec_list:
                sec_label = sec.get("label")
                items = sec.get("items") or []
                if cur_page[cur_col] and cur_used[cur_col] + section_header_h > available_h:
                    if cur_col + 1 < text_cols:
                        cur_col += 1
                    else:
                        pages.append(_rebalance_two_col_page(cur_page))
                        cur_page = [[] for _ in range(text_cols)]
                        cur_used = [0.0 for _ in range(text_cols)]
                        cur_col = 0
                cur_page[cur_col].append(("section", {"label": sec_label}))
                cur_used[cur_col] += section_header_h
                for g in items:
                    gh = estimate_group_h_text(g, text_col_w)
                    if cur_page[cur_col] and cur_used[cur_col] + gh + row_gap > available_h:
                        if cur_col + 1 < text_cols:
                            cur_col += 1
                            cur_page[cur_col].append(("section-continued", {"label": sec_label, "continued": True}))
                            cur_used[cur_col] += section_header_h
                        else:
                            pages.append(_rebalance_two_col_page(cur_page))
                            cur_page = [[] for _ in range(text_cols)]
                            cur_used = [0.0 for _ in range(text_cols)]
                            cur_col = 0
                            cur_page[cur_col].append(("section-continued", {"label": sec_label, "continued": True}))
                            cur_used[cur_col] += section_header_h
                    cur_page[cur_col].append(("group", g))
                    cur_used[cur_col] += gh + row_gap
                cur_used[cur_col] += sec_gap
            if any(col for col in cur_page):
                pages.append(_rebalance_two_col_page(cur_page))
        else:
            cur_page = []
            cur_used = 0.0
            for sec in sec_list:
                items = sec.get("items") or []
                if cur_page and cur_used + section_header_h > available_h:
                    pages.append(cur_page)
                    cur_page = []
                    cur_used = 0.0
                cur_page.append(("section", sec))
                cur_used += section_header_h
                for g in items:
                    gh = estimate_group_h(g)
                    if cur_page and cur_used + gh + row_gap > available_h:
                        pages.append(cur_page)
                        cur_page = [("section-continued", {"label": sec.get("label"), "continued": True})]
                        cur_used = section_header_h
                    cur_page.append(("group", g))
                    cur_used += gh + row_gap
                cur_used += sec_gap
            if cur_page:
                pages.append(cur_page)

        def draw_section_header(y, label, continued=False, x_left=None, x_right=None):
            txt = str(label or "").strip().upper()
            if continued:
                txt += " · CONTINUED" if lang == "en" else " · FORTSETTER"
            txt = txt[:42]
            left = x_left if x_left is not None else content_left
            right = x_right if x_right is not None else content_right
            text_y = y - 3.8 * mm
            text_w = _draw_tracked_text(left, text_y, txt, "Helvetica", section_size - 0.2, tracking=0.75, centered=False, color=colors.HexColor(styled_section_hex))
            line_x = left + text_w + 3.2 * mm
            c.setStrokeColor(LINE_COLOR)
            c.setLineWidth(0.9)
            if right - line_x > 6 * mm:
                c.line(line_x, text_y + 1.3 * mm, right, text_y + 1.3 * mm)
            return text_y - 4.8 * mm

        if is_styled_grid:
            flat_grid = []
            for sec in sec_list:
                sec_label = str(sec.get("label") or "").strip()
                first_in_section = True
                for g in (sec.get("items") or []):
                    gg = dict(g)
                    gg["section_display"] = sec_label if first_in_section else ""
                    flat_grid.append(gg)
                    first_in_section = False
            grid_gap_x = 18 * mm if size == "a4" else 22 * mm
            grid_gap_y = row_gap
            grid_cols = 2 if styled_columns == 2 else 1
            grid_card_w = (content_w - (grid_gap_x * (grid_cols - 1))) / max(1, grid_cols)
            grid_card_h = row_min_h
            rows_fit = max(1, int((available_h + grid_gap_y) // (grid_card_h + grid_gap_y)))

            def _layout_fill_pages(items, cols, top_y):
                if cols <= 1:
                    return [[(g, 0, idx, top_y - idx * (grid_card_h + grid_gap_y)) for idx, g in enumerate(items)]] if items else [[]]
                pages = []
                idx = 0
                bottom_safety = content_bottom + (6 * mm)
                while idx < len(items):
                    placements = []
                    col = 0
                    y_cursor = top_y
                    first_in_col = True
                    row_in_col = 0
                    while idx < len(items):
                        g = items[idx]
                        sec_label = str(g.get("section_display") or "").strip()
                        # In fill-left-first mode, continuation cards in the same section
                        # should visually stay tighter together than section-to-section jumps.
                        # Because grid cards keep an internal section band for consistent image
                        # sizing, use a smaller external gap for continuation cards here.
                        # Keep continuation dishes in the same section noticeably tighter
                        # than the jump to a new section when using Fill left first.
                        fill_same_section_gap = (0.25 * mm if size == "a4" else 0.4 * mm)
                        fill_new_section_gap = (sec_gap if sec_gap > row_gap else row_gap + (1.6 * mm if size == "a4" else 2.0 * mm))
                        gap_before = 0 if first_in_col else (fill_new_section_gap if sec_label else fill_same_section_gap)
                        candidate_top = y_cursor - gap_before
                        candidate_bottom = candidate_top - grid_card_h
                        if candidate_bottom < bottom_safety:
                            if col == 0:
                                col = 1
                                y_cursor = top_y
                                first_in_col = True
                                row_in_col = 0
                                continue
                            break
                        placements.append((g, col, row_in_col, candidate_top))
                        y_cursor = candidate_bottom
                        first_in_col = False
                        row_in_col += 1
                        idx += 1
                    if not placements and idx < len(items):
                        placements.append((items[idx], 0, 0, top_y))
                        idx += 1
                    pages.append(placements)
                return pages or [[]]

            top_y = content_top_start
            if grid_cols == 2 and styled_flow == 'fill':
                grid_pages = _layout_fill_pages(flat_grid, grid_cols, top_y)
            else:
                per_page = max(grid_cols, rows_fit * grid_cols)
                grid_pages = [flat_grid[i:i+per_page] for i in range(0, len(flat_grid), per_page)] or [[]]
            total_pages = len(grid_pages)
            for page_idx, page_groups in enumerate(grid_pages, start=1):
                top_y = draw_page_shell(page_idx)
                if grid_cols == 2 and styled_flow == 'fill':
                    placements = page_groups
                else:
                    page_count = len(page_groups)
                    left_count = math.ceil(page_count / 2) if grid_cols == 2 else page_count
                    placements = []
                    if grid_cols == 1:
                        y_cursor = top_y
                        first_in_col = True
                        row = 0
                        same_section_gap = max(0.8 * mm, row_gap * 0.5)
                        for g in page_groups:
                            sec_label = str(g.get("section_display") or "").strip()
                            gap_before = 0 if first_in_col else (sec_gap if sec_label else same_section_gap)
                            card_y_top = y_cursor - gap_before
                            placements.append((g, 0, row, card_y_top))
                            y_cursor = card_y_top - grid_card_h
                            first_in_col = False
                            row += 1
                    else:
                        for idx, g in enumerate(page_groups):
                            if styled_flow == 'row':
                                row = idx // grid_cols
                                col = idx % grid_cols
                            else:
                                if idx < left_count:
                                    col = 0
                                    row = idx
                                else:
                                    col = 1
                                    row = idx - left_count
                            card_y_top = top_y - row * (grid_card_h + grid_gap_y)
                            placements.append((g, col, row, card_y_top))
                for g, col, row, card_y_top in placements:
                    card_x = content_left + col * (grid_card_w + grid_gap_x)
                    card_yb = card_y_top - grid_card_h
                    c.setFillColor(CARD_FILL)
                    c.roundRect(card_x, card_yb, grid_card_w, grid_card_h, 4.8 * mm, stroke=0, fill=1)

                    inner_pad = 2.6 * mm
                    sec_label = str(g.get("section_display") or "").strip().upper()[:22]
                    base_section_band_h = 6.0 * mm if size == "a4" else 7.4 * mm
                    # Keep a consistent internal vertical rhythm for all cards,
                    # even when the section label is only shown on the first card
                    # in a section. This avoids taller-looking continuation images
                    # and keeps spacing aligned with the other menu variants.
                    # Slightly more section-band height gives a bit more breathing
                    # room between the section label and the first dish content.
                    section_band_h = base_section_band_h
                    card_top = card_yb + grid_card_h
                    sec_y = card_top - inner_pad - 2.8 * mm
                    if sec_label:
                        sec_w = _draw_tracked_text(card_x + inner_pad, sec_y, sec_label, "Helvetica", section_size - 1.0, tracking=0.55, centered=False, color=colors.HexColor(styled_section_hex))
                        sec_line_x = card_x + inner_pad + sec_w + 2.4 * mm
                        c.setStrokeColor(LINE_COLOR)
                        c.setLineWidth(0.8)
                        if card_x + grid_card_w - inner_pad - sec_line_x > 5 * mm:
                            c.line(sec_line_x, sec_y + 1.0 * mm, card_x + grid_card_w - inner_pad, sec_y + 1.0 * mm)
                    img_x = card_x + inner_pad
                    img_y = card_yb + inner_pad
                    img_h = grid_card_h - 2 * inner_pad - section_band_h
                    draw_thumb(
                        g.get("image_path"),
                        img_x,
                        img_y,
                        thumb_w,
                        img_h,
                        g.get("image_focal_x") or 50.0,
                        g.get("image_focal_y") or 50.0,
                        g.get("image_zoom") or 120.0,
                    )
                    tx = img_x + thumb_w + 3.0 * mm
                    price_x = card_x + grid_card_w - inner_pad
                    tw = max(24 * mm, price_x - tx - 14 * mm)
                    title_lines = _wrap_lines(str(g.get("title") or ""), tw, "Helvetica-Bold", name_size - 0.2)[:2] or [""]
                    desc_lines = _wrap_lines(str(g.get("desc") or ""), tw, "Times-Italic", desc_size)[:2]
                    opts = g.get("options") or []
                    opt_line = " • ".join([str(o.get("label") or "").strip() for o in opts[:3] if str(o.get("label") or "").strip()])
                    ty = card_top - inner_pad - section_band_h - 3.0 * mm
                    first_title_y = ty
                    c.setFillColor(colors.HexColor(styled_body_hex))
                    c.setFont("Helvetica-Bold", name_size - 0.2)
                    for ln in title_lines:
                        c.drawString(tx, ty, ln)
                        ty -= 3.7 * mm
                    price_txt = group_price_text(g)
                    if price_txt:
                        c.setFillColor(PRICE_COLOR)
                        c.setFont(PRICE_FONT, price_size - 0.2)
                        c.drawRightString(price_x, first_title_y, price_txt)
                    if desc_lines:
                        c.setFillColor(colors.HexColor(styled_desc_hex))
                        c.setFont("Times-Italic", desc_size)
                        for ln in desc_lines:
                            c.drawString(tx, ty, ln)
                            ty -= 3.0 * mm
                    if opt_line:
                        ty -= 0.8 * mm
                        c.setFillColor(colors.HexColor(styled_desc_hex))
                        c.setFont("Helvetica", desc_size - 0.1)
                        opt_lines = _wrap_lines(opt_line, tw, "Helvetica", desc_size - 0.1)[:2]
                        for ln in opt_lines:
                            c.drawString(tx, ty, ln)
                            ty -= 3.1 * mm
                draw_styled_footer(page_idx, total_pages)
                c.showPage()
            c.save()
            pdf.seek(0)
            return pdf

        total_pages = max(1, len(pages))
        for page_idx, page_items in enumerate(pages, start=1):
            if is_styled_text:
                top_y = draw_page_shell(page_idx)
                for col_idx in range(text_cols):
                    col_items = page_items[col_idx] if col_idx < len(page_items) else []
                    col_left = content_left + col_idx * (text_col_w + text_gap)
                    col_right = col_left + text_col_w
                    y = top_y
                    for kind, obj in col_items:
                        if kind.startswith("section"):
                            y -= 1.2 * mm
                            y = draw_section_header(y, obj.get("label"), continued=(kind == "section-continued"), x_left=col_left, x_right=col_right)
                            continue
                        g = obj
                        price_txt = group_price_text(g)
                        title_lines = _wrap_lines(str(g.get("title") or ""), text_col_w - 18 * mm, "Helvetica-Bold", name_size)[:2] or [""]
                        desc_lines = _wrap_lines(str(g.get("desc") or ""), text_col_w - 2 * mm, "Times-Italic", desc_size)[:2]
                        opts = g.get("options") or []
                        block_h = estimate_group_h_text(g, text_col_w)
                        card_yb = y - block_h
                        c.setFillColor(CARD_FILL)
                        c.roundRect(col_left, card_yb, text_col_w, block_h, 4.2 * mm, stroke=0, fill=1)
                        tx = col_left + 3.2 * mm
                        price_x = col_right - 3.2 * mm
                        ty = y - 4.4 * mm
                        first_title_y = ty
                        c.setFillColor(colors.HexColor(styled_body_hex))
                        c.setFont("Helvetica-Bold", name_size)
                        for ln in title_lines:
                            c.drawString(tx, ty, ln)
                            ty -= 3.9 * mm
                        if price_txt:
                            c.setFillColor(PRICE_COLOR)
                            c.setFont(PRICE_FONT, price_size)
                            c.drawRightString(price_x, first_title_y, price_txt)
                        if desc_lines:
                            c.setFillColor(colors.HexColor(styled_desc_hex))
                            c.setFont("Times-Italic", desc_size)
                            for ln in desc_lines:
                                c.drawString(tx, ty, ln)
                                ty -= 3.25 * mm
                            ty -= 0.8 * mm
                        if opts:
                            c.setFillColor(colors.HexColor(styled_desc_hex))
                            c.setFont("Helvetica", desc_size)
                            for o in opts[:8]:
                                label = str(o.get("label") or "").strip()
                                if not label:
                                    continue
                                opt_price = fmt_price(o.get("price")) if o.get("price") is not None else ""
                                c.drawString(tx, ty, f"• {label}"[:48])
                                if opt_price:
                                    c.drawRightString(price_x, ty, opt_price)
                                ty -= 3.5 * mm
                        y = card_yb - row_gap
                    # Two-column Styled Menu · Text uses whitespace-only separation,
                    # like a restaurant menu with "invisible" columns.
                    if text_cols == 2 and col_idx == 0:
                        pass
                draw_styled_footer(page_idx, total_pages)
                c.showPage()
                continue

            y = draw_page_shell(page_idx)
            for kind, obj in page_items:
                if kind.startswith("section"):
                    y -= 1.2 * mm
                    y = draw_section_header(y, obj.get("label"), continued=(kind == "section-continued"))
                    continue

                g = obj
                block_h = estimate_group_h(g)
                card_yb = y - block_h
                card_radius = 5.0 * mm
                c.setFillColor(CARD_FILL)
                c.roundRect(content_left, card_yb, content_w, block_h, card_radius, stroke=0, fill=1)

                draw_thumb(
                    g.get("image_path"),
                    content_left,
                    card_yb,
                    thumb_w,
                    block_h,
                    g.get("image_focal_x") or 50.0,
                    g.get("image_focal_y") or 50.0,
                    g.get("image_zoom") or 120.0,
                )

                tx = content_left + thumb_w + 3.6 * mm
                price_x = content_right - 3.6 * mm
                tw = max(30 * mm, price_x - tx - 16 * mm)
                title_lines = _wrap_lines(str(g.get("title") or ""), tw, "Helvetica-Bold", name_size)[:2] or [""]
                desc_lines = _wrap_lines(str(g.get("desc") or ""), tw, "Helvetica", desc_size)[:2]
                title_line_h = 3.9 * mm
                desc_line_h = 3.3 * mm
                text_block_h = (len(title_lines) * title_line_h) + (len(desc_lines) * desc_line_h)
                ty = card_yb + (block_h + text_block_h) / 2.0 - 2.8 * mm
                first_title_y = ty

                c.setFillColor(colors.HexColor(styled_body_hex))
                c.setFont("Helvetica-Bold", name_size)
                for ln in title_lines:
                    c.drawString(tx, ty, ln)
                    ty -= title_line_h

                if desc_lines:
                    c.setFillColor(colors.HexColor(styled_desc_hex))
                    c.setFont("Times-Italic", desc_size)
                    for ln in desc_lines:
                        c.drawString(tx, ty, ln)
                        ty -= desc_line_h

                price_txt = group_price_text(g)
                if price_txt:
                    c.setFillColor(PRICE_COLOR)
                    c.setFont(PRICE_FONT, price_size)
                    c.drawRightString(price_x, first_title_y, price_txt)

                y = card_yb - row_gap
            draw_styled_footer(page_idx, total_pages)
            c.showPage()

        c.save()
        pdf.seek(0)
        return pdf

    if style == "grid":
        bg = colors.HexColor("#191a1f")
        c.setFillColor(bg)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#f0c36a"))
        c.rect(margin, H - margin - 6 * mm, W - 2 * margin, 3 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24 if size == "a4" else 32)
        c.drawCentredString(W / 2.0, H - margin - 14 * mm, title[:34])
        if subtitle:
            c.setFillColor(colors.HexColor("#c2c7cf"))
            c.setFont("Helvetica", 10 if size == "a4" else 12)
            c.drawCentredString(W / 2.0, H - margin - 20 * mm, subtitle[:66])
        flat = []
        for sec in sections:
            for g in (sec.get("items") or []):
                gg = dict(g)
                gg["section_display"] = sec.get("label") or ""
                flat.append(gg)
        chosen = [g for g in flat if g.get("image_path")] or flat
        chosen = chosen[:8 if size == "a4" else 10]
        cols = 2
        gap_x = 7 * mm
        gap_y = 6 * mm
        top = H - margin - 28 * mm
        bottom = margin + 24 * mm
        rows = max(1, math.ceil(len(chosen) / cols))
        card_w = (W - 2 * margin - gap_x) / 2.0
        card_h = min(42 * mm if size == "a4" else 50 * mm, (top - bottom - gap_y * (rows - 1)) / max(1, rows))
        img_h = card_h * 0.60
        for idx, g in enumerate(chosen):
            row = idx // cols
            col = idx % cols
            x = margin + col * (card_w + gap_x)
            y = top - (row + 1) * card_h - row * gap_y
            c.setFillColor(colors.HexColor("#24262d"))
            c.roundRect(x, y, card_w, card_h, 4 * mm, stroke=0, fill=1)
            path = g.get("image_path")
            if path is not None:
                try:
                    img = Image.open(path)
                    img2 = _cover_crop_adjusted(img, max(220, int(card_w)), max(120, int(img_h)), float(g.get("image_focal_x") or 50), float(g.get("image_focal_y") or 50), float(g.get("image_zoom") or 120))
                    pth = c.beginPath()
                    pth.roundRect(x, y + card_h - img_h, card_w, img_h, 4 * mm)
                    c.saveState()
                    c.clipPath(pth, stroke=0, fill=0)
                    c.drawImage(ImageReader(img2), x, y + card_h - img_h, width=card_w, height=img_h, mask="auto")
                    c.restoreState()
                except Exception:
                    pass
            sec_label = str(g.get("section_display") or "").strip()
            if sec_label:
                c.setFillColor(colors.HexColor("#f0c36a"))
                c.setFont("Helvetica-Bold", 8 if size == "a4" else 9)
                c.drawString(x + 4 * mm, y + card_h - img_h - 5 * mm, sec_label.upper()[:22])
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 10 if size == "a4" else 12)
            ty = y + card_h - img_h - 12 * mm
            for line in _wrap_lines(str(g.get("title") or ""), card_w - 12 * mm, "Helvetica-Bold", 10 if size == "a4" else 12)[:2]:
                c.drawString(x + 4 * mm, ty, line)
                ty -= 10
            opts = [o for o in (g.get("options") or []) if o.get("price") is not None]
            price_txt = fmt_price(g.get("from_price"), prefix_from=(len(opts) > 1)) if opts else ""
            if price_txt:
                c.setFillColor(colors.HexColor("#f0c36a"))
                c.setFont("Helvetica-Bold", 10 if size == "a4" else 12)
                c.drawRightString(x + card_w - 4 * mm, y + 5 * mm, price_txt)
        c.drawImage(ImageReader(qr_img), W - margin - 18 * mm, margin + 2 * mm, width=14 * mm, height=14 * mm, mask="auto")
        c.setFillColor(colors.HexColor("#c2c7cf"))
        c.setFont("Helvetica", 8)
        c.drawString(margin, margin + 9, "Scan for full menu" if lang == "en" else "Skann for full meny")
        c.showPage()
        c.save()
        pdf.seek(0)
        return pdf

    if style == "sections":
        c.setFillColor(colors.HexColor("#fbf7f0"))
        c.rect(0, 0, W, H, stroke=0, fill=1)
        frame_x = margin
        frame_y = margin
        frame_w = W - 2 * margin
        frame_h = H - 2 * margin
        c.setStrokeColor(FRAME_COLOR)
        c.setLineWidth(1)
        c.roundRect(frame_x, frame_y, frame_w, frame_h, 4 * mm, stroke=1, fill=0)
        y = H - margin - 10
        c.setFillColor(NAME_COLOR)
        c.setFont("Helvetica-Bold", 20 if size == "a4" else 26)
        c.drawString(frame_x + 8 * mm, y, title[:40])
        if subtitle:
            c.setFillColor(MUTED_COLOR)
            c.setFont("Helvetica", 10 if size == "a4" else 12)
            c.drawString(frame_x + 8 * mm, y - 14, subtitle[:68])
        hero_y = y - 42 * mm
        hero_h2 = 28 * mm if size == "a4" else 40 * mm
        if hero_reader is not None:
            pth = c.beginPath()
            pth.roundRect(frame_x + 8 * mm, hero_y, frame_w - 16 * mm, hero_h2, 3 * mm)
            c.saveState()
            c.clipPath(pth, stroke=0, fill=0)
            c.drawImage(hero_reader, frame_x + 8 * mm, hero_y, width=frame_w - 16 * mm, height=hero_h2, mask="auto")
            c.restoreState()
            c.setStrokeColor(FRAME_COLOR)
            c.roundRect(frame_x + 8 * mm, hero_y, frame_w - 16 * mm, hero_h2, 3 * mm, stroke=1, fill=0)
        sec_y = hero_y - 10 * mm
        visible_sections = [sec for sec in sections if (sec.get("items") or [])][:4]
        block_gap = 5 * mm
        block_h = (sec_y - (frame_y + 24 * mm) - block_gap * (len(visible_sections)-1)) / max(1, len(visible_sections))
        for sec in visible_sections:
            block_h_use = max(22 * mm, block_h)
            x = frame_x + 8 * mm
            yb = sec_y - block_h_use
            c.setFillColor(colors.white)
            c.roundRect(x, yb, frame_w - 16 * mm, block_h_use, 3 * mm, stroke=0, fill=1)
            c.setStrokeColor(LIGHT_LINE_COLOR)
            c.roundRect(x, yb, frame_w - 16 * mm, block_h_use, 3 * mm, stroke=1, fill=0)
            items = sec.get("items") or []
            item0 = next((g for g in items if g.get("image_path")), items[0] if items else None)
            thumb_w = 26 * mm if size == "a4" else 32 * mm
            if item0 and item0.get("image_path"):
                try:
                    img = Image.open(item0.get("image_path"))
                    img2 = _cover_crop_adjusted(img, max(160, int(thumb_w)), max(120, int(block_h_use - 6 * mm)), float(item0.get("image_focal_x") or 50), float(item0.get("image_focal_y") or 50), float(item0.get("image_zoom") or 120))
                    pth = c.beginPath()
                    pth.roundRect(x + 3 * mm, yb + 3 * mm, thumb_w, block_h_use - 6 * mm, 2.5 * mm)
                    c.saveState()
                    c.clipPath(pth, stroke=0, fill=0)
                    c.drawImage(ImageReader(img2), x + 3 * mm, yb + 3 * mm, width=thumb_w, height=block_h_use - 6 * mm, mask="auto")
                    c.restoreState()
                except Exception:
                    pass
            tx = x + thumb_w + 7 * mm
            ty = yb + block_h_use - 6 * mm
            c.setFillColor(SECTION_COLOR)
            c.setFont("Helvetica-Bold", 9 if size == "a4" else 11)
            c.drawString(tx, ty, str(sec.get("label") or "").upper()[:26])
            ty -= 11
            c.setFillColor(BODY_COLOR)
            c.setFont("Helvetica-Bold", 9 if size == "a4" else 10)
            for g in items[:3]:
                nm = str(g.get("title") or "")
                opts = [o for o in (g.get("options") or []) if o.get("price") is not None]
                price_txt = fmt_price(g.get("from_price"), prefix_from=(len(opts) > 1)) if opts else ""
                c.drawString(tx, ty, nm[:32])
                if price_txt:
                    c.setFillColor(SECTION_COLOR)
                    c.drawRightString(x + frame_w - 20 * mm, ty, price_txt)
                    c.setFillColor(BODY_COLOR)
                ty -= 10
                if ty < yb + 5 * mm:
                    break
            sec_y = yb - block_gap
        c.drawImage(ImageReader(qr_img), frame_x + frame_w - 22 * mm, frame_y + 4 * mm, width=15 * mm, height=15 * mm, mask="auto")
        c.setFillColor(BODY_COLOR)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(frame_x + 8 * mm, frame_y + 13 * mm, "Contact" if lang == "en" else "Kontakt")
        c.setFillColor(MUTED_COLOR)
        c.setFont("Helvetica", 8)
        contact_line = contact.get("phone") or ("@" + str(contact.get("instagram") or "") if contact.get("instagram") else (contact.get("email") or ""))
        if contact_line:
            c.drawString(frame_x + 8 * mm, frame_y + 4 * mm, str(contact_line)[:72])
        c.showPage()
        c.save()
        pdf.seek(0)
        return pdf

    # Visual poster: one-page customer-facing layout with hero + selected dishes
    c.setFillColorRGB(0.985, 0.972, 0.952)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    card_x = margin
    card_y = margin
    card_w = W - 2 * margin
    card_h = H - 2 * margin
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(card_x, card_y, card_w, card_h, 8 * mm, stroke=0, fill=1)

    top_y = H - margin
    if hero_reader is not None:
        img_h = 58 * mm if size == "a4" else 82 * mm
        c.drawImage(hero_reader, card_x, top_y - img_h, width=card_w, height=img_h, mask="auto")
        c.setFillColorRGB(0, 0, 0)
        c.setFillAlpha(0.22)
        c.roundRect(card_x, top_y - img_h, card_w, img_h, 8 * mm, stroke=0, fill=1)
        c.setFillAlpha(1)
        badge_w = 28 * mm if size == "a4" else 34 * mm
        badge_h = 10 * mm if size == "a4" else 12 * mm
        c.setFillColorRGB(0.98, 0.93, 0.85)
        c.roundRect(card_x + 10 * mm, top_y - 15 * mm, badge_w, badge_h, 3 * mm, stroke=0, fill=1)
        c.setFillColorRGB(0.36, 0.24, 0.08)
        c.setFont("Helvetica-Bold", 8 if size == "a4" else 9)
        c.drawString(card_x + 13 * mm, top_y - 11.5 * mm, ("MENU HIGHLIGHTS" if lang == "en" else "MENYHØYDEPUNKTER"))
        title_y = top_y - 23 * mm
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 22 if size == "a4" else 30)
        c.drawString(card_x + 10 * mm, title_y, title[:44])
        c.setFont("Helvetica", 10 if size == "a4" else 12)
        if subtitle:
            c.drawString(card_x + 10 * mm, title_y - 12, subtitle[:70])
        grid_top = top_y - img_h - 10 * mm
    else:
        c.setFillColorRGB(0.08, 0.10, 0.12)
        c.setFont("Helvetica-Bold", 22 if size == "a4" else 30)
        c.drawString(card_x + 10 * mm, top_y - 14 * mm, title[:44])
        if subtitle:
            c.setFillColorRGB(0.35, 0.38, 0.42)
            c.setFont("Helvetica", 10 if size == "a4" else 12)
            c.drawString(card_x + 10 * mm, top_y - 20 * mm, subtitle[:70])
        grid_top = top_y - 30 * mm

    section_count = len([sec for sec in sections if (sec.get("items") or []) and (sec.get("label") or "").strip()])
    flat = []
    for sec in sections:
        for g in sec.get("items") or []:
            gg = dict(g)
            gg["section_display"] = sec.get("label") or ""
            flat.append(gg)
    max_cards = 6 if size == "a4" else 8
    # Prefer a broader customer-facing selection across sections when possible.
    selected = []
    by_section = {}
    for g in flat:
        by_section.setdefault(g.get("section_display") or "", []).append(g)
    ordered_sections = [sec.get("label") or "" for sec in sections if (sec.get("items") or [])]
    for sec_label in ordered_sections:
        items = by_section.get(sec_label) or []
        if items:
            selected.append(items[0])
            if len(selected) >= max_cards:
                break
    if len(selected) < max_cards:
        seen = {g.get("key") for g in selected}
        for g in flat:
            if g.get("key") in seen:
                continue
            selected.append(g)
            seen.add(g.get("key"))
            if len(selected) >= max_cards:
                break
    cols = 2
    gap_x = 6 * mm
    gap_y = 7 * mm
    qr_size = 24 * mm if size == "a4" else 30 * mm
    footer_band_h = 36 * mm
    grid_bottom = card_y + footer_band_h + 8 * mm
    rows = max(1, math.ceil(len(selected) / cols))
    card_gap_total = gap_y * (rows - 1)
    item_h = max(34 * mm, (grid_top - grid_bottom - card_gap_total) / rows)
    item_w = (card_w - 20 * mm - gap_x) / cols
    img_h = item_h * 0.55

    for idx, g in enumerate(selected):
        row = idx // cols
        col = idx % cols
        x = card_x + 10 * mm + col * (item_w + gap_x)
        y = grid_top - (row + 1) * item_h - row * gap_y
        c.setFillColorRGB(0.99, 0.985, 0.978)
        c.roundRect(x, y, item_w, item_h, 4 * mm, stroke=0, fill=1)
        p = g.get("image_path")
        if p is not None:
            try:
                img = Image.open(p)
                img2 = _cover_crop_adjusted(img, max(240, int(item_w)), max(120, int(img_h)), float(g.get("image_focal_x") or 50), float(g.get("image_focal_y") or 50), float(g.get("image_zoom") or 120))
                c.drawImage(ImageReader(img2), x, y + item_h - img_h, width=item_w, height=img_h, mask="auto")
            except Exception:
                pass
        c.setFillColorRGB(0.58, 0.42, 0.16)
        c.setFont("Helvetica-Bold", 8 if size == "a4" else 9)
        sec_label = str(g.get("section_display") or "").strip()
        if sec_label:
            c.drawString(x + 4 * mm, y + item_h - img_h - 5 * mm, sec_label.upper()[:22])
        c.setFillColorRGB(0.08, 0.10, 0.12)
        c.setFont("Helvetica-Bold", 11 if size == "a4" else 13)
        title_lines = _wrap_lines(str(g.get("title") or ""), item_w - 16 * mm, "Helvetica-Bold", 11 if size == "a4" else 13)[:2]
        ty = y + item_h - img_h - 12 * mm
        for line in title_lines:
            c.drawString(x + 4 * mm, ty, line)
            ty -= 10
        opts = [o for o in (g.get("options") or []) if o.get("price") is not None]
        price_line = fmt_price(g.get("from_price"), prefix_from=(len(opts) > 1)) if opts else ""
        if price_line:
            c.setFillColorRGB(0.58, 0.42, 0.16)
            c.setFont("Helvetica-Bold", 10 if size == "a4" else 12)
            c.drawRightString(x + item_w - 4 * mm, y + 6 * mm, price_line)
        desc = (g.get("desc") or "").strip()
        if desc:
            c.setFillColorRGB(0.35, 0.38, 0.42)
            c.setFont("Helvetica", 8 if size == "a4" else 9)
            for line in _wrap_lines(desc, item_w - 10 * mm, "Helvetica", 8 if size == "a4" else 9)[:2]:
                c.drawString(x + 4 * mm, ty, line)
                ty -= 8

    # footer CTA band
    band_y = card_y + 6 * mm
    c.setFillColorRGB(0.97, 0.94, 0.89)
    c.roundRect(card_x + 8 * mm, band_y, card_w - 16 * mm, footer_band_h - 6 * mm, 5 * mm, stroke=0, fill=1)
    c.drawImage(ImageReader(qr_img), card_x + card_w - 8 * mm - qr_size, band_y + 4 * mm, width=qr_size, height=qr_size, mask="auto")
    c.setFillColorRGB(0.08, 0.10, 0.12)
    c.setFont("Helvetica-Bold", 14 if size == "a4" else 16)
    c.drawString(card_x + 14 * mm, band_y + footer_band_h - 16 * mm, ("Scan to see the full menu" if lang == "en" else "Skann for å se hele menyen"))
    c.setFillColorRGB(0.35, 0.38, 0.42)
    c.setFont("Helvetica", 9 if size == "a4" else 10)
    c.drawString(card_x + 14 * mm, band_y + footer_band_h - 27 * mm, url[:80])
    dish_word = "dishes" if lang == "en" else "retter"
    sec_word = "sections" if lang == "en" else "seksjoner"
    summary = f"{len(groups)} {dish_word} · {section_count} {sec_word}" if section_count else f"{len(groups)} {dish_word}"
    c.drawString(card_x + 14 * mm, band_y + 8 * mm, summary[:60])

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf



def _resolve_menu_poster_request(token: str, with_image: int, lang: str, size: str, style: str, max_dishes: int):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")

    lang = (lang or "en").lower().strip()
    if lang not in ("en", "no"):
        lang = "en"
    size = (size or "a4").lower().strip()
    if size not in ("a4", "a3"):
        size = "a4"

    style = (style or "").lower().strip()
    if style not in ("text", "hero", "visual", "styled", "styled_text", "styled_grid", "grid", "sections"):
        style = "hero" if bool(with_image) else "text"

    try:
        max_dishes = int(max_dishes or 0)
    except Exception:
        max_dishes = 0
    if max_dishes < 0:
        max_dishes = 0

    return listing, lang, size, style, max_dishes


@app.get("/api/owner/{token}/menu-poster.pdf")
def owner_menu_poster_pdf(
    token: str,
    request: Request,
    lang: str = "en",
    size: str = "a4",
    with_image: int = 0,
    style: str = "",
    download: int = 1,
    name_color: str = "",
    section_color: str = "",
    body_color: str = "",
    frame_color: str = "",
    max_dishes: int = 0,
    hero_focal_x: float = 50.0,
    hero_focal_y: float = 50.0,
    hero_zoom: float = 100.0,
    styled_bg_color: str = "",
    styled_card_color: str = "",
    styled_name_color: str = "",
    styled_section_color: str = "",
    styled_body_color: str = "",
    styled_desc_color: str = "",
    styled_line_color: str = "",
    styled_columns: int = 1,
    styled_flow: str = "column",
):
    """Download a print-friendly menu poster generated from the current menu.

    Available for both Basic and Premium (uses the same owner token as the dashboard).
    """
    listing, lang, size, style, max_dishes = _resolve_menu_poster_request(token, with_image, lang, size, style, max_dishes)

    pdf = _make_menu_poster_pdf(listing, request, lang=lang, size=size, style=style, name_color=name_color, section_color=section_color, body_color=body_color, frame_color=frame_color, max_dishes=max_dishes, hero_focal_x=hero_focal_x, hero_focal_y=hero_focal_y, hero_zoom=hero_zoom, styled_bg_color=styled_bg_color, styled_card_color=styled_card_color, styled_name_color=styled_name_color, styled_section_color=styled_section_color, styled_body_color=styled_body_color, styled_desc_color=styled_desc_color, styled_line_color=styled_line_color, styled_columns=styled_columns, styled_flow=styled_flow)
    style_tag = "" if style == "text" else f"-{style}"
    fn = f"{listing.get('slug')}-menu{style_tag}-{lang}-{size}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.get("/api/owner/{token}/menu-poster.png")
def owner_menu_poster_png(
    token: str,
    request: Request,
    lang: str = "en",
    size: str = "a4",
    with_image: int = 0,
    style: str = "",
    download: int = 1,
    name_color: str = "",
    section_color: str = "",
    body_color: str = "",
    frame_color: str = "",
    max_dishes: int = 0,
    hero_focal_x: float = 50.0,
    hero_focal_y: float = 50.0,
    hero_zoom: float = 100.0,
    styled_bg_color: str = "",
    styled_card_color: str = "",
    styled_name_color: str = "",
    styled_section_color: str = "",
    styled_body_color: str = "",
    styled_desc_color: str = "",
    styled_line_color: str = "",
    styled_columns: int = 1,
    styled_flow: str = "column",
    dpi: int = 180,
):
    listing, lang, size, style, max_dishes = _resolve_menu_poster_request(token, with_image, lang, size, style, max_dishes)

    try:
        import fitz  # PyMuPDF
    except Exception as exc:
        raise HTTPException(status_code=500, detail="PNG export requires PyMuPDF. Run pip install -r requirements.txt again.") from exc

    dpi = max(96, min(int(dpi or 180), 300))
    pdf = _make_menu_poster_pdf(listing, request, lang=lang, size=size, style=style, name_color=name_color, section_color=section_color, body_color=body_color, frame_color=frame_color, max_dishes=max_dishes, hero_focal_x=hero_focal_x, hero_focal_y=hero_focal_y, hero_zoom=hero_zoom, styled_bg_color=styled_bg_color, styled_card_color=styled_card_color, styled_name_color=styled_name_color, styled_section_color=styled_section_color, styled_body_color=styled_body_color, styled_desc_color=styled_desc_color, styled_line_color=styled_line_color, styled_columns=styled_columns, styled_flow=styled_flow)

    doc = fitz.open(stream=pdf.getvalue(), filetype="pdf")
    try:
        page = doc.load_page(0)
        scale = dpi / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        png_bytes = pix.tobytes("png")
    finally:
        doc.close()

    style_tag = "" if style == "text" else f"-{style}"
    fn = f"{listing.get('slug')}-menu{style_tag}-{lang}-{size}.png"
    headers = {}
    if int(download or 0):
        headers["Content-Disposition"] = f'attachment; filename="{fn}"'
    return Response(content=png_bytes, media_type="image/png", headers=headers)





def _first_nonempty(*vals):
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _listing_area_line(listing: dict) -> str:
    return f"{listing.get('area','')} · {listing.get('city','')}".strip(" ·")


def _promo_palette(plan: str = "standard"):
    base = _brand_colors(plan)
    if _normalize_plan(plan) in ("growth", "pro"):
        return {
            **base,
            "soft": (0.95, 0.97, 1.0),
            "soft2": (0.89, 0.93, 1.0),
            "panel": (0.97, 0.98, 1.0),
            "warm": (0.98, 0.96, 0.92),
        }
    return {
        **base,
        "soft": (0.94, 0.98, 0.97),
        "soft2": (0.87, 0.95, 0.93),
        "panel": (0.98, 0.99, 0.98),
        "warm": (0.98, 0.96, 0.92),
    }


def _backend_effective_menu_image(listing: dict, dish: dict) -> str:
    """Mirror the frontend's demo image fallback logic for poster rendering.

    This keeps Poster 3 consistent with the public page, especially for the
    Maria demo listing where a few curated dish photos are used for testing.
    """
    img = str(dish.get("image") or dish.get("photo") or dish.get("img") or dish.get("hero_image") or "").strip()
    raw = dish.get("name") if dish.get("name") is not None else dish.get("title")
    if isinstance(raw, dict):
        title = str(raw.get("en") or raw.get("no") or "").lower()
    else:
        title = str(raw or "").lower()
    slug = str((listing or {}).get("slug") or "")
    if slug == "marias-filipino-kusina":
        if "adobo" in title:
            return "assets/dish_adobo_custom.png"
        if "lumpia" in title or "vårr" in title or "värr" in title:
            return "assets/dish_lumpia_custom.png"
        if "barkada" in title:
            return "assets/dish_barkada_custom.png"
        if "dish_lumpia" in img:
            return "assets/dish_lumpia_custom.png"
        if "dish_family3" in img or "dish_barkada" in img:
            return "assets/dish_barkada_custom.png"
    return img


def _menu_image_candidates(listing: dict) -> list:
    """Return distinct menu photos in menu order.

    We dedupe on the *resolved effective* path so repeated menu variants like
    single/family/group do not collapse the whole selection to one visible dish
    unless they truly use the exact same photo. We also try to keep one photo
    per distinct dish key/title first, which helps Poster 3 surface multiple
    menu items automatically.
    """
    menu = listing.get("menu") or []
    preferred = []
    fallback = []
    seen_paths = set()
    seen_dishes = set()

    def _dish_identity(m: dict) -> str:
        key = str(m.get("dish_key") or "").strip().lower()
        if key:
            return key
        raw = m.get("name") if m.get("name") is not None else m.get("title")
        if isinstance(raw, dict):
            txt = str(raw.get("en") or raw.get("no") or "").strip().lower()
        else:
            txt = str(raw or "").strip().lower()
        return txt

    for m in menu:
        if not isinstance(m, dict):
            continue
        raw = _backend_effective_menu_image(listing, m)
        if not raw:
            continue
        ident = _dish_identity(m)
        if raw not in seen_paths and ident and ident not in seen_dishes:
            preferred.append(raw)
            seen_paths.add(raw)
            seen_dishes.add(ident)
        elif raw not in seen_paths:
            fallback.append(raw)
            seen_paths.add(raw)

    out = preferred + fallback
    return out


def _resolve_marketing_image_paths(listing: dict, limit: int = 3) -> list:
    paths = []
    for raw in _menu_image_candidates(listing):
        path = _resolve_public_image_path(raw)
        if path and path.exists():
            paths.append(path)
            if len(paths) >= limit:
                break
    return paths


def _draw_cover_photo(c, path_or_img, x: float, y: float, w: float, h: float):
    try:
        if hasattr(path_or_img, 'convert'):
            img = path_or_img.convert('RGB')
        else:
            img = Image.open(str(path_or_img)).convert('RGB')
        img2 = _cover_crop(img, max(1, int(w)), max(1, int(h)))
        c.drawImage(ImageReader(img2), x, y, width=w, height=h, mask='auto')
        return True
    except Exception:
        return False


def _draw_stacked_photo_strip(c, listing: dict, x: float, y: float, w: float, h: float, gap_mm: float = 3.5):
    paths = _resolve_marketing_image_paths(listing, limit=3)
    if not paths:
        return _draw_hero_block(c, listing, x, y, w, h)
    gap = gap_mm * mm
    if len(paths) == 1:
        return _draw_cover_photo(c, paths[0], x, y, w, h)
    if len(paths) == 2:
        col_w = (w - gap) / 2
        ok1 = _draw_cover_photo(c, paths[0], x, y, col_w, h)
        ok2 = _draw_cover_photo(c, paths[1], x + col_w + gap, y, col_w, h)
        return ok1 or ok2
    left_w = w * 0.58
    right_w = w - left_w - gap
    half_h = (h - gap) / 2
    ok = False
    ok = _draw_cover_photo(c, paths[0], x, y, left_w, h) or ok
    ok = _draw_cover_photo(c, paths[1], x + left_w + gap, y + half_h + gap, right_w, half_h) or ok
    ok = _draw_cover_photo(c, paths[2], x + left_w + gap, y, right_w, half_h) or ok
    return ok


def _fit_font_size(text: str, max_width: float, font_name: str, start_size: int, min_size: int = 10) -> int:
    size = start_size
    txt = text or ''
    while size > min_size and stringWidth(txt, font_name, size) > max_width:
        size -= 1
    return size


def _truncate_with_ellipsis(text: str, max_width: float, font_name: str, font_size: int) -> str:
    txt = str(text or '')
    if stringWidth(txt, font_name, font_size) <= max_width:
        return txt
    ell = '…'
    while txt and stringWidth(txt + ell, font_name, font_size) > max_width:
        txt = txt[:-1]
    return (txt + ell) if txt else ell

def _safe_contact_line(listing: dict) -> str:
    try:
        contact = listing.get("contact") or {}
    except Exception:
        return ""
    if isinstance(contact, str):
        return contact.strip()
    if not isinstance(contact, dict):
        return ""
    if contact.get("phone"):
        return str(contact.get("phone"))
    if contact.get("whatsapp"):
        return f"WhatsApp: {contact.get('whatsapp')}"
    if contact.get("instagram"):
        return f"@{contact.get('instagram')}"
    if contact.get("email"):
        return str(contact.get("email"))
    return ""


def _get_signature_dish(listing: dict, lang: str = "en") -> tuple[str, str, str]:
    menu = listing.get("menu") or []
    sig = None
    for m in menu:
        tags = m.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if any(str(t).lower().strip() == "signature" for t in tags):
            sig = m
            break
    if sig is None and menu:
        sig = menu[0]
    if not sig:
        return ("", "", "")

    raw_title = sig.get("title") if sig.get("title") is not None else sig.get("name")
    if isinstance(raw_title, dict):
        title = str(raw_title.get(lang) or raw_title.get("en") or raw_title.get("no") or "").strip()
    else:
        title = str(raw_title or "").strip()

    raw_desc = sig.get("desc")
    if isinstance(raw_desc, dict):
        desc = str(raw_desc.get(lang) or raw_desc.get("en") or raw_desc.get("no") or "").strip()
    else:
        desc = str(raw_desc or "").strip()

    price = ""
    p = sig.get("price")
    if p is None:
        serves = sig.get("serves") or []
        if isinstance(serves, list) and serves:
            first = serves[0] or {}
            if isinstance(first, dict):
                p = first.get("price")
    if p is not None:
        currency = str(listing.get("currency") or "").strip()
        try:
            price = f"{int(p)} {currency}".strip()
        except Exception:
            price = f"{p} {currency}".strip()
    return (title, desc, price)


def _brand_colors(plan: str = "standard"):
    plan = _normalize_plan(plan)
    if plan in ("growth", "pro"):
        return {
            "accent": (0.31, 0.42, 0.93),
            "accent2": (0.92, 0.95, 1.0),
            "ink": (0.10, 0.12, 0.16),
            "muted": (0.38, 0.41, 0.46),
            "line": (0.86, 0.89, 0.94),
        }
    return {
        "accent": (0.16, 0.52, 0.47),
        "accent2": (0.92, 0.97, 0.96),
        "ink": (0.10, 0.12, 0.16),
        "muted": (0.38, 0.41, 0.46),
        "line": (0.86, 0.89, 0.91),
    }


def _draw_hero_block(c, listing: dict, x: float, y: float, w: float, h: float):
    hero_path = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    if not hero_path:
        hero_path = _resolve_public_image_path("assets/portal_hero.jpg")
    try:
        if hero_path and hero_path.exists():
            img = Image.open(str(hero_path)).convert("RGB")
            img2 = _cover_crop(img, max(1, int(w)), max(1, int(h)))
            c.drawImage(ImageReader(img2), x, y, width=w, height=h, mask="auto")
            return True
    except Exception:
        return False
    return False


def _listing_photo_paths(listing: dict) -> list[Path]:
    paths: list[Path] = []
    hero = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    if hero and hero.exists():
        paths.append(hero)
    for item in (listing.get("menu") or []):
        if not isinstance(item, dict):
            continue
        p = _resolve_public_image_path(str(item.get("image") or ""))
        if p and p.exists() and p not in paths:
            paths.append(p)
    return paths


def _signature_image_path(listing: dict) -> Optional[Path]:
    direct = _resolve_public_image_path(str(listing.get("signature_image") or ""))
    if direct and direct.exists():
        return direct
    menu = listing.get("menu") or []
    for item in menu:
        if not isinstance(item, dict):
            continue
        tags = item.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if any(str(t).lower().strip() == "signature" for t in tags):
            p = _resolve_public_image_path(str(item.get("image") or ""))
            if p and p.exists():
                return p
    for item in menu:
        if not isinstance(item, dict):
            continue
        p = _resolve_public_image_path(str(item.get("image") or ""))
        if p and p.exists():
            return p
    return _resolve_public_image_path(str(listing.get("hero_image") or ""))


def _draw_cover_photo(c, img_path: Optional[Path], x: float, y: float, w: float, h: float, radius: float = 0):
    if not img_path or not img_path.exists():
        return False
    try:
        img = Image.open(str(img_path)).convert("RGB")
        img2 = _cover_crop(img, max(1, int(w)), max(1, int(h)))
        c.drawImage(ImageReader(img2), x, y, width=w, height=h, mask="auto")
        return True
    except Exception:
        return False


def _hex_to_rgb01(value: str, fallback=(0.52, 0.34, 0.78)):
    s = str(value or '').strip()
    if s.startswith('#'):
        s = s[1:]
    if len(s) == 3:
        s = ''.join(ch * 2 for ch in s)
    if len(s) != 6:
        return fallback
    try:
        r = int(s[0:2], 16) / 255.0
        g = int(s[2:4], 16) / 255.0
        b = int(s[4:6], 16) / 255.0
        return (r, g, b)
    except Exception:
        return fallback


def _rgb01_to_hex(rgb, fallback='#69453a'):
    try:
        if not isinstance(rgb, (tuple, list)) or len(rgb) != 3:
            return fallback
        r = max(0, min(255, int(round(float(rgb[0]) * 255))))
        g = max(0, min(255, int(round(float(rgb[1]) * 255))))
        b = max(0, min(255, int(round(float(rgb[2]) * 255))))
        return f'#{r:02x}{g:02x}{b:02x}'
    except Exception:
        return fallback




def _set_safe_font(c, primary: str, size: float, fallback: str = "Helvetica"):
    try:
        c.setFont(primary, size)
        return primary
    except Exception:
        c.setFont(fallback, size)
        return fallback

def _localized_listing_text(listing: dict, key: str, lang: str, default: str = '') -> str:
    raw = listing.get(key)
    if isinstance(raw, dict):
        return str(raw.get(lang) or raw.get('en') or raw.get('no') or default or '').strip()
    if raw is None:
        return str(default or '').strip()
    return str(raw or default or '').strip()


def _flyer_headline_lines(listing: dict, lang: str) -> list[str]:
    custom = _localized_listing_text(listing, 'flyer_headline', lang, '')
    if custom:
        out = [line.strip() for line in custom.splitlines() if line.strip()]
        return out[:4] if out else []
    return [
        'FRESH HOMEMADE', 'ASIAN MEALS', 'NEAR YOU'
    ] if lang == 'en' else [
        'FERSKE HJEMMELAGDE', 'ASIATISKE RETTER', 'NÆR DEG'
    ]


def _flyer_support_text(listing: dict, lang: str) -> str:
    custom = _localized_listing_text(listing, 'flyer_support', lang, '')
    if custom:
        return custom
    return _poster_tagline(listing, lang) or ('Discover the menu, see the dishes and order in seconds.' if lang == 'en' else 'Oppdag menyen, se rettene og bestill på få sekunder.')


def _draw_cover_photo_adjusted(c, img_path: Optional[Path], x: float, y: float, w: float, h: float, focal_x: float = 50, focal_y: float = 50, zoom: float = 100):
    if not img_path or not img_path.exists():
        return False
    try:
        img = Image.open(str(img_path)).convert('RGB')
        iw, ih = img.size
        if iw <= 1 or ih <= 1:
            return False
        target_ratio = max(0.01, float(w) / max(1.0, float(h)))
        img_ratio = iw / ih
        if img_ratio >= target_ratio:
            base_h = ih
            base_w = ih * target_ratio
        else:
            base_w = iw
            base_h = iw / target_ratio
        zoom = max(100.0, min(200.0, float(zoom or 100)))
        crop_w = max(1, min(iw, int(round(base_w * (100.0 / zoom)))))
        crop_h = max(1, min(ih, int(round(base_h * (100.0 / zoom)))))
        fx = max(0.0, min(100.0, float(focal_x or 50))) / 100.0
        fy = max(0.0, min(100.0, float(focal_y or 50))) / 100.0
        x0 = int(round((iw - crop_w) * fx))
        y0 = int(round((ih - crop_h) * fy))
        x0 = max(0, min(iw - crop_w, x0))
        y0 = max(0, min(ih - crop_h, y0))
        img2 = img.crop((x0, y0, x0 + crop_w, y0 + crop_h)).resize((max(1, int(w)), max(1, int(h))), Image.Resampling.LANCZOS)
        c.drawImage(ImageReader(img2), x, y, width=w, height=h, mask='auto')
        return True
    except Exception:
        return False


def _fit_photo(img_path: Optional[Path], target_w: int, target_h: int) -> Optional[Image.Image]:
    if not img_path or not img_path.exists():
        return None
    try:
        img = Image.open(str(img_path)).convert("RGB")
        return ImageOps.contain(img, (max(1, target_w), max(1, target_h)))
    except Exception:
        return None


def _draw_contain_photo(c, img_path: Optional[Path], x: float, y: float, w: float, h: float):
    img = _fit_photo(img_path, int(w), int(h))
    if img is None:
        return False
    iw, ih = img.size
    dx = x + (w - iw) / 2
    dy = y + (h - ih) / 2
    c.drawImage(ImageReader(img), dx, dy, width=iw, height=ih, mask="auto")
    return True


def _draw_badge(c, x: float, y: float, text: str, fill_rgb, ink_rgb=(1, 1, 1), pad_x: float = 4.5 * mm, h: float = 8 * mm, radius: float = 4 * mm, font_size: int = 8):
    text = str(text or "").strip()
    if not text:
        return 0
    tw = c.stringWidth(text, "Helvetica-Bold", font_size)
    w = tw + 2 * pad_x
    c.setFillColorRGB(*fill_rgb)
    c.roundRect(x, y, w, h, radius, stroke=0, fill=1)
    c.setFillColorRGB(*ink_rgb)
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(x + pad_x, y + (h - font_size) / 2 + 1.2, text)
    return w


def _poster3_headline(listing: dict, lang: str = "en") -> str:
    custom = _localized_listing_text(listing, 'poster3_headline', lang, '')
    if custom:
        return custom.strip()
    fallback = _localized_listing_text(listing, 'flyer_headline', lang, '')
    if fallback:
        return str(fallback).replace('\n', ' ').strip()
    return 'FRESH HOMEMADE ASIAN MEALS' if lang == 'en' else 'FERSKE HJEMMELAGDE ASIATISKE RETTER'


def _poster3_support(listing: dict, lang: str = "en") -> str:
    custom = _localized_listing_text(listing, 'poster3_support', lang, '')
    if custom:
        return custom.strip()
    fallback = _flyer_support_text(listing, lang)
    if fallback:
        return fallback.strip()
    return 'Discover the menu, find your favorites, and order with confidence.' if lang == 'en' else 'Oppdag menyen, finn favorittene dine og bestill trygt.'


def _draw_circle_photo(c, path: Optional[Path], cx: float, cy: float, diameter: float, border_rgb=(1,1,1), border_mm: float = 2.2):
    border = border_mm * mm
    c.setFillColorRGB(*border_rgb)
    c.circle(cx, cy, diameter/2 + border, stroke=0, fill=1)
    c.saveState()
    clip = c.beginPath()
    clip.circle(cx, cy, diameter/2)
    c.clipPath(clip, stroke=0, fill=0)
    ok = _draw_cover_photo(c, path, cx - diameter/2, cy - diameter/2, diameter, diameter)
    if not ok:
        c.setFillColorRGB(0.93, 0.92, 0.90)
        c.circle(cx, cy, diameter/2, stroke=0, fill=1)
    c.restoreState()
    return ok


def _poster4_headline(listing: dict, lang: str = "en") -> str:
    custom = _localized_listing_text(listing, 'poster4_headline', lang, '')
    if custom:
        return custom.strip()
    fallback = _localized_listing_text(listing, 'poster3_headline', lang, '')
    if fallback:
        return fallback.strip()
    return 'AUTHENTIC HOMEMADE ASIAN FAVORITES' if lang == 'en' else 'AUTENTISKE HJEMMELAGDE ASIATISKE FAVORITTER'


def _poster4_support(listing: dict, lang: str = "en") -> str:
    custom = _localized_listing_text(listing, 'poster4_support', lang, '')
    if custom:
        return custom.strip()
    fallback = _localized_listing_text(listing, 'poster3_support', lang, '')
    if fallback:
        return fallback.strip()
    return 'Fresh dishes, trusted pickup, and a full menu one scan away.' if lang == 'en' else 'Ferske retter, trygg henting og full meny bare én skann unna.'


def _draw_roundrect_photo(c, path: Optional[Path], x: float, y: float, w: float, h: float, radius: float, border_rgb=(1,1,1), border_mm: float = 1.8, rotation_deg: float = 0):
    border = border_mm * mm
    c.saveState()
    if rotation_deg:
        cx = x + w/2
        cy = y + h/2
        c.translate(cx, cy)
        c.rotate(rotation_deg)
        x = -w/2
        y = -h/2
    c.setFillColorRGB(*border_rgb)
    c.roundRect(x - border, y - border, w + 2*border, h + 2*border, radius + border, stroke=0, fill=1)
    c.saveState()
    clip = c.beginPath()
    clip.roundRect(x, y, w, h, radius)
    c.clipPath(clip, stroke=0, fill=0)
    ok = _draw_cover_photo(c, path, x, y, w, h)
    if not ok:
        c.setFillColorRGB(0.93, 0.92, 0.90)
        c.roundRect(x, y, w, h, radius, stroke=0, fill=1)
    c.restoreState()
    c.restoreState()
    return ok


def _draw_diamond_photo(c, path: Optional[Path], cx: float, cy: float, size: float, border_rgb=(1,1,1), border_mm: float = 2.0, corner_radius_mm: float = 5.2, focal_x: float = 50, focal_y: float = 50, zoom: float = 120):
    border = border_mm * mm
    radius = corner_radius_mm * mm
    half = size / 2
    c.saveState()
    c.translate(cx, cy)

    # Keep the frame as a 45° diamond, but clip the photo INSIDE that frame.
    # The photo itself is rotated back so it stays upright/horizontal.
    c.saveState()
    c.rotate(45)
    c.setFillColorRGB(*border_rgb)
    c.roundRect(-half - border, -half - border, size + 2*border, size + 2*border, radius + border, stroke=0, fill=1)
    clip = c.beginPath()
    clip.roundRect(-half, -half, size, size, radius)
    c.clipPath(clip, stroke=0, fill=0)

    # Rotate back so the image content is upright inside the diamond clip.
    c.rotate(-45)

    # Oversize the image box so the diamond is fully filled and the photo is
    # slightly zoomed in instead of leaving corners exposed.
    img_box = size * 1.48
    img_half = img_box / 2
    ok = _draw_cover_photo_adjusted(c, path, -img_half, -img_half, img_box, img_box, focal_x=focal_x, focal_y=focal_y, zoom=zoom)
    if not ok:
        c.setFillColorRGB(0.93, 0.92, 0.90)
        c.rect(-img_half, -img_half, img_box, img_box, stroke=0, fill=1)
    c.restoreState()
    c.restoreState()
    return ok


def _poster4_signature_font_name() -> str:
    """Register a more elegant title font for Poster 4 if available."""
    font_name = "Poster4Signature"
    try:
        pdfmetrics.getFont(font_name)
        return font_name
    except Exception:
        pass
    candidates = [
        "/usr/share/fonts/truetype/ebgaramond/EBGaramond12-Italic.ttf",
        "/usr/share/fonts/truetype/ebgaramond/EBGaramond08-Italic.ttf",
    ]
    for font_path in candidates:
        try:
            if Path(font_path).exists():
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                return font_name
        except Exception:
            continue
    return "Times-Italic"


def _make_flyer4_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    title = str(listing.get("name") or ("Kitchen" if lang == "en" else "Kjøkken")).strip()
    url = _public_listing_url(request, listing.get("slug") or "")
    accent = _hex_to_rgb01(listing.get("poster4_accent") or listing.get("poster3_accent") or listing.get("flyer_accent") or "#f39a21")
    dark = (0.08, 0.08, 0.10)
    soft_text = (0.84, 0.85, 0.88)

    hero_path = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    img_paths = _resolve_marketing_image_paths(listing, limit=3)
    if hero_path and hero_path.exists() and hero_path not in img_paths:
        img_paths = [hero_path] + img_paths
    if not img_paths and hero_path and hero_path.exists():
        img_paths = [hero_path]
    if not img_paths:
        img_paths = [None, None, None]
    while len(img_paths) < 3:
        img_paths.append(img_paths[-1])
    img_paths = img_paths[:3]

    top_fx = max(0.0, min(100.0, float(listing.get("poster4_top_image_focal_x") or 50)))
    top_fy = max(0.0, min(100.0, float(listing.get("poster4_top_image_focal_y") or 50)))
    top_zoom = max(100.0, min(200.0, float(listing.get("poster4_top_image_zoom") or 120)))
    left_fx = max(0.0, min(100.0, float(listing.get("poster4_left_image_focal_x") or 50)))
    left_fy = max(0.0, min(100.0, float(listing.get("poster4_left_image_focal_y") or 50)))
    left_zoom = max(100.0, min(200.0, float(listing.get("poster4_left_image_zoom") or 120)))
    right_fx = max(0.0, min(100.0, float(listing.get("poster4_right_image_focal_x") or 50)))
    right_fy = max(0.0, min(100.0, float(listing.get("poster4_right_image_focal_y") or 50)))
    right_zoom = max(100.0, min(200.0, float(listing.get("poster4_right_image_zoom") or 120)))

    headline = _poster4_headline(listing, lang)
    support = _poster4_support(listing, lang)
    contact_line = _safe_contact_line(listing) or url.replace('https://','').replace('http://','')

    menu_titles = []
    for item in (listing.get('menu') or []):
        if not isinstance(item, dict):
            continue
        raw = item.get('title') if item.get('title') is not None else item.get('name')
        if isinstance(raw, dict):
            txt = str(raw.get(lang) or raw.get('en') or raw.get('no') or '').strip()
        else:
            txt = str(raw or '').strip()
        if txt and txt not in menu_titles:
            menu_titles.append(txt)
        if len(menu_titles) >= 6:
            break
    if not menu_titles:
        menu_titles = ["Fresh homemade favorites"] if lang == 'en' else ["Hjemmelagde favoritter"]
    ink_color = "#161616"
    bg_color = "#f7f1e8"

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")

    margin = 10 * mm
    art_x = margin
    art_y = margin
    art_w = W - 2 * margin
    art_h = H - 2 * margin

    # Outer frame should be black rather than orange/yellow.
    c.setFillColorRGB(*dark)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColorRGB(*dark)
    c.roundRect(art_x, art_y, art_w, art_h, 5*mm, stroke=0, fill=1)

    center_x = art_x + art_w/2
    # Poster 4: precise diamond geometry.
    # - Larger diamonds that can crop outside the black artboard
    # - Slight air/gap between the three diamonds
    # - Entire cluster pushed upward so the top diamond is clipped similarly
    #   to the side diamonds
    # - Smaller center circle
    cluster_cy = art_y + art_h - 104 * mm
    diamond_size = 108 * mm
    hub_r = 44 * mm

    tip_offset = diamond_size / (2 ** 0.5)
    gap = 6.5 * mm
    positions = [
        (center_x, cluster_cy + tip_offset + gap),
        (center_x - tip_offset - gap, cluster_cy),
        (center_x + tip_offset + gap, cluster_cy),
    ]

    crop_specs = [
        (top_fx, top_fy, top_zoom),
        (left_fx, left_fy, left_zoom),
        (right_fx, right_fy, right_zoom),
    ]
    for idx, (px, py) in enumerate(positions):
        fx, fy, zm = crop_specs[idx]
        _draw_diamond_photo(c, img_paths[idx], px, py, diamond_size, border_rgb=(1,1,1), border_mm=1.6, focal_x=fx, focal_y=fy, zoom=zm)

    # Center hub: thin white ring + black inner circle.
    ring_outer_r = hub_r + 0.8*mm
    ring_inner_r = hub_r - 0.2*mm
    c.setFillColorRGB(1,1,1)
    c.circle(center_x, cluster_cy, ring_outer_r, stroke=0, fill=1)
    c.setFillColorRGB(*dark)
    c.circle(center_x, cluster_cy, ring_inner_r, stroke=0, fill=1)

    max_title_w = ring_inner_r * 1.56
    signature_font = _poster4_signature_font_name()
    title_font = max(12, min(30, int(round(float(listing.get("poster4_title_font_size") or 20)))))
    title_lines_all = _wrap_lines(title, max_title_w, signature_font, title_font)
    title_lines = title_lines_all[:3]
    if len(title_lines) >= 3 and len(title_lines_all) > 3:
        title_lines[-1] = _truncate_with_ellipsis(title_lines[-1], max_title_w, signature_font, title_font)
    line_step = 6.6 * mm
    total_h = len(title_lines) * line_step
    start_y = cluster_cy + (total_h/2) - 4.5*mm
    c.setFillColorRGB(*accent)
    c.setFont(signature_font, title_font)
    y = start_y
    for line in title_lines:
        tw = stringWidth(line, signature_font, title_font)
        c.drawString(center_x - tw/2, y, line)
        y -= line_step

    head_y = art_y + 112 * mm
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 20)
    for line in _wrap_lines(headline, art_w - 50*mm, "Helvetica-Bold", 20)[:3]:
        tw = stringWidth(line, "Helvetica-Bold", 20)
        c.drawString(center_x - tw/2, head_y, line)
        head_y -= 8.1 * mm

    support_top = head_y - 1.5 * mm
    c.setFillColorRGB(*soft_text)
    c.setFont("Helvetica", 11.6)
    for line in _wrap_lines(support, art_w - 58*mm, "Helvetica", 11.6)[:4]:
        tw = stringWidth(line, "Helvetica", 11.6)
        c.drawString(center_x - tw/2, support_top, line)
        support_top -= 5.6 * mm

    # More air and better symmetry in the lower section.
    body_top = support_top - 12 * mm
    side_pad = 24 * mm
    col_gap = 18 * mm
    col_w = (art_w - (2 * side_pad) - col_gap) / 2
    left_x = art_x + side_pad
    right_x = left_x + col_w + col_gap

    # Reserve clean space for up to 6 visible dishes.
    yy = body_top
    c.setFillColorRGB(*accent)
    c.setFont("Helvetica-Bold", 13)
    left_label = "POPULAR PICKS" if lang == 'en' else 'POPULÆRE RETTER'
    c.drawString(left_x, yy, left_label)
    yy -= 8.0 * mm
    c.setFont("Helvetica-Bold", 10.6)
    c.setFillColorRGB(1,1,1)
    max_visible_items = 6
    item_step = 6.15 * mm
    for t in menu_titles[:max_visible_items]:
        c.setFillColorRGB(*accent)
        c.circle(left_x + 1.7*mm, yy + 1.2*mm, 1.2*mm, stroke=0, fill=1)
        c.setFillColorRGB(1,1,1)
        c.drawString(left_x + 5*mm, yy, _truncate_with_ellipsis(t, col_w - 8*mm, "Helvetica-Bold", 10.8))
        yy -= item_step

    c.setFillColorRGB(*accent)
    c.setFont("Helvetica-Bold", 13)
    right_label = "SCAN FULL MENU" if lang == 'en' else 'SKANN HELE MENYEN'
    right_label_w = stringWidth(right_label, "Helvetica-Bold", 13)
    qr_size = 33 * mm
    qr_x = right_x + (col_w - qr_size) / 2
    # Lift QR so its top aligns roughly with the first menu item line.
    qr_top = body_top - 9 * mm + 2 * mm
    qr_y = qr_top - qr_size
    c.drawString(right_x + (col_w - right_label_w) / 2, body_top, right_label)
    c.drawInlineImage(qr_img, qr_x, qr_y, qr_size, qr_size)

    footer_line_y = art_y + 19 * mm
    c.setStrokeColorRGB(*accent)
    c.setLineWidth(0.8)
    c.line(art_x + 22*mm, footer_line_y, art_x + art_w - 22*mm, footer_line_y)

    footer_text_y = footer_line_y - 9 * mm
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(art_x + 22*mm, footer_text_y, _truncate_with_ellipsis(title.upper(), art_w*0.55, "Helvetica-Bold", 12))
    c.setFillColorRGB(*soft_text)
    c.setFont("Helvetica", 9.7)
    footer_text_y -= 6 * mm
    for line in _wrap_lines(contact_line, art_w - 44*mm, "Helvetica", 9.7)[:2]:
        c.drawString(art_x + 22*mm, footer_text_y, line)
        footer_text_y -= 4.8 * mm

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _make_flyer3_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    title = str(listing.get("name") or ("Kitchen" if lang == "en" else "Kjøkken")).strip()
    url = _public_listing_url(request, listing.get("slug") or "")
    accent = _hex_to_rgb01(listing.get("poster3_accent") or listing.get("flyer_accent") or "#f39a21")
    dark = (0.15, 0.14, 0.18)
    warm_white = (0.985, 0.98, 0.965)
    soft_text = (0.83, 0.86, 0.92)
    
    hero_path = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    img_paths = _resolve_marketing_image_paths(listing, limit=3)
    if not img_paths and hero_path and hero_path.exists():
        img_paths = [hero_path]
    if not img_paths:
        img_paths = [None, None, None]
    while len(img_paths) < 3:
        img_paths.append(img_paths[-1])

    headline = _poster3_headline(listing, lang)
    support = _poster3_support(listing, lang)
    contact_line = _safe_contact_line(listing) or url.replace('https://','').replace('http://','')
    ink_color = "#161616"
    bg_color = "#f7f1e8"

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = None

    margin = 11 * mm
    art_x = margin
    art_y = margin
    art_w = W - 2 * margin
    art_h = H - 2 * margin

    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Outer card
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(art_x, art_y, art_w, art_h, 8 * mm, stroke=0, fill=1)

    left_w = art_w * 0.58
    panel_x = art_x + art_w * 0.54
    panel_w = art_x + art_w - panel_x

    # Hero image as the design foundation on the left side, clipped to the poster card.
    c.saveState()
    outer_clip = c.beginPath()
    outer_clip.roundRect(art_x, art_y, art_w, art_h, 8 * mm)
    c.clipPath(outer_clip, stroke=0, fill=0)
    if not _draw_cover_photo(c, hero_path or img_paths[0], art_x, art_y, left_w + 12 * mm, art_h):
        c.setFillColorRGB(0.92, 0.91, 0.88)
        c.rect(art_x, art_y, left_w + 12 * mm, art_h, stroke=0, fill=1)
    c.restoreState()

    # Orange flowing fields on top of the hero image.
    orange_field = c.beginPath()
    orange_field.moveTo(art_x, art_y)
    orange_field.lineTo(art_x + left_w - 22 * mm, art_y)
    orange_field.curveTo(art_x + left_w - 38 * mm, art_y + art_h * 0.22, art_x + left_w - 34 * mm, art_y + art_h * 0.82, art_x + left_w - 10 * mm, art_y + art_h)
    orange_field.lineTo(art_x, art_y + art_h)
    orange_field.close()
    c.setFillColorRGB(*accent)
    c.drawPath(orange_field, stroke=0, fill=1)

    # Main image window cut through the orange field.
    hero_window = c.beginPath()
    hero_window.moveTo(art_x + 28 * mm, art_y + art_h)
    hero_window.lineTo(art_x + left_w + 8 * mm, art_y + art_h)
    hero_window.curveTo(art_x + left_w - 24 * mm, art_y + art_h * 0.82, art_x + left_w - 20 * mm, art_y + art_h * 0.24, art_x + left_w + 5 * mm, art_y)
    hero_window.lineTo(art_x + 20 * mm, art_y)
    hero_window.curveTo(art_x + 56 * mm, art_y + art_h * 0.26, art_x + 50 * mm, art_y + art_h * 0.76, art_x + 28 * mm, art_y + art_h)
    hero_window.close()
    c.setFillColorRGB(1, 1, 1)
    c.drawPath(hero_window, stroke=0, fill=1)

    c.saveState()
    hero_img_clip = c.beginPath()
    hero_img_clip.moveTo(art_x + 28 * mm, art_y + art_h)
    hero_img_clip.lineTo(art_x + left_w + 6 * mm, art_y + art_h)
    hero_img_clip.curveTo(art_x + left_w - 26 * mm, art_y + art_h * 0.82, art_x + left_w - 22 * mm, art_y + art_h * 0.24, art_x + left_w + 3 * mm, art_y)
    hero_img_clip.lineTo(art_x + 22 * mm, art_y)
    hero_img_clip.curveTo(art_x + 56 * mm, art_y + art_h * 0.26, art_x + 52 * mm, art_y + art_h * 0.76, art_x + 28 * mm, art_y + art_h)
    hero_img_clip.close()
    c.clipPath(hero_img_clip, stroke=0, fill=0)
    if not _draw_cover_photo(c, hero_path or img_paths[0], art_x + 14 * mm, art_y, left_w + 8 * mm, art_h):
        c.setFillColorRGB(0.93, 0.92, 0.90)
        c.rect(art_x + 14 * mm, art_y, left_w + 8 * mm, art_h, stroke=0, fill=1)
    c.restoreState()

    # Thin white ribbon between left and right for a cleaner transition.
    ribbon = c.beginPath()
    ribbon.moveTo(panel_x - 5.5 * mm, art_y)
    ribbon.curveTo(panel_x - 12 * mm, art_y + art_h * 0.24, panel_x - 12 * mm, art_y + art_h * 0.76, panel_x - 4.5 * mm, art_y + art_h)
    ribbon.lineTo(panel_x - 0.6 * mm, art_y + art_h)
    ribbon.curveTo(panel_x - 6.5 * mm, art_y + art_h * 0.76, panel_x - 6.5 * mm, art_y + art_h * 0.24, panel_x + 0.8 * mm, art_y)
    ribbon.close()
    c.setFillColorRGB(1, 1, 1)
    c.drawPath(ribbon, stroke=0, fill=1)

    # Dark info panel with a single smooth curved edge.
    panel = c.beginPath()
    panel.moveTo(panel_x + 5 * mm, art_y)
    panel.lineTo(art_x + art_w, art_y)
    panel.lineTo(art_x + art_w, art_y + art_h)
    panel.lineTo(panel_x + 7 * mm, art_y + art_h)
    panel.curveTo(panel_x - 6 * mm, art_y + art_h * 0.78, panel_x - 6 * mm, art_y + art_h * 0.22, panel_x + 5 * mm, art_y)
    panel.close()
    c.setFillColorRGB(*dark)
    c.drawPath(panel, stroke=0, fill=1)

    # Two menu circles with a tighter horizontal relationship and more vertical spread.
    circles = [
        (art_x + 43 * mm, art_y + 167 * mm, 35 * mm),
        (art_x + 56 * mm, art_y + 88 * mm, 37 * mm),
    ]
    for idx, (cx, cy, d) in enumerate(circles):
        _draw_circle_photo(c, img_paths[idx], cx, cy, d, border_rgb=(1, 1, 1), border_mm=2.1)

    # Left headline block: larger, elegant, consistent white script styling.
    left_text_x = art_x + 14 * mm
    fresh_text = "Fresh" if lang == "en" else "Fersk"
    food_text = "Food"
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Times-Italic", 39)
    c.drawString(left_text_x + 6 * mm, art_y + 44 * mm, fresh_text)
    c.drawString(left_text_x + 29 * mm, art_y + 22.5 * mm, food_text)

    # Right content.
    inner_x = panel_x + 19 * mm
    inner_right = art_x + art_w - 16 * mm
    inner_top = art_y + art_h - 18 * mm

    c.setFillColorRGB(*accent)
    c.setFont("Helvetica-Bold", 10.8)
    c.drawString(inner_x, inner_top, _truncate_with_ellipsis(title.upper(), inner_right - inner_x, "Helvetica-Bold", 10.8))

    c.setFillColorRGB(1, 1, 1)
    head_fs = 17
    head_lines = _wrap_lines(headline, inner_right - inner_x, "Helvetica-Bold", head_fs)[:4]
    y = inner_top - 12 * mm
    c.setFont("Helvetica-Bold", head_fs)
    for line in head_lines:
        c.drawString(inner_x, y, line)
        y -= 7.1 * mm

    c.setFillColorRGB(*soft_text)
    support_fs = 10
    support_lh = 4.8 * mm
    c.setFont("Helvetica", support_fs)
    # Let the support copy breathe further down toward the menu area, instead of
    # cutting it off after only a few short lines.
    provisional_menu_y = art_y + 88 * mm
    available_support_h = max(12 * mm, (y - 1.3 * mm) - (provisional_menu_y + 10 * mm))
    max_support_lines = max(4, int(available_support_h / support_lh))
    support_lines = _wrap_lines(support, inner_right - inner_x - 1 * mm, "Helvetica", support_fs)[:max_support_lines]
    y -= 1.3 * mm
    for line in support_lines:
        c.drawString(inner_x, y, line)
        y -= support_lh

    menu_titles = []
    for item in (listing.get('menu') or []):
        if not isinstance(item, dict):
            continue
        raw = item.get('title') if item.get('title') is not None else item.get('name')
        if isinstance(raw, dict):
            txt = str(raw.get(lang) or raw.get('en') or raw.get('no') or '').strip()
        else:
            txt = str(raw or '').strip()
        if txt and txt not in menu_titles:
            menu_titles.append(txt)
        if len(menu_titles) >= 5:
            break
    if not menu_titles:
        menu_titles = ["Fresh homemade favorites"] if lang == 'en' else ["Hjemmelagde favoritter"]

    # Move the menu somewhat back up so the right side feels more balanced,
    # while still leaving a generous support-text area above it.
    section_y = max(art_y + 106 * mm, min(y - 6 * mm, art_y + 119 * mm))
    c.setFillColorRGB(*accent)
    c.roundRect(inner_x, section_y + 1.4 * mm, 17 * mm, 1.5 * mm, 0.8 * mm, stroke=0, fill=1)
    c.roundRect(inner_x + 35 * mm, section_y + 1.4 * mm, max(20 * mm, inner_right - (inner_x + 35 * mm)), 1.5 * mm, 0.8 * mm, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(inner_x + 19 * mm, section_y - 0.2 * mm, "MENU" if lang == 'en' else "MENY")

    c.setFont("Helvetica", 10.1)
    yy = section_y - 7.8 * mm
    item_step = 6.0 * mm
    for t in menu_titles:
        t = _truncate_with_ellipsis(t, (inner_right - inner_x) - 1 * mm, "Helvetica", 10.1)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(inner_x, yy, t)
        dots_start = inner_x + min(stringWidth(t, "Helvetica", 10.1) + 4 * mm, (inner_right - inner_x) - 14 * mm)
        dots_end = inner_right
        if dots_end - dots_start > 10 * mm:
            c.setStrokeColorRGB(0.88, 0.75, 0.46)
            c.setLineWidth(0.6)
            c.setDash(0.8 * mm, 1.0 * mm)
            c.line(dots_start, yy + 1.4 * mm, dots_end, yy + 1.4 * mm)
            c.setDash()
        yy -= item_step

    footer_x = panel_x + 13 * mm
    footer_y = art_y + 11 * mm
    footer_w = panel_w - 26 * mm
    footer_h = 36 * mm
    c.setFillColorRGB(0.11, 0.12, 0.16)
    c.roundRect(footer_x, footer_y, footer_w, footer_h, 6 * mm, stroke=0, fill=1)

    qr_size = 22 * mm
    qx = footer_x + 6.5 * mm
    qy = footer_y + (footer_h - qr_size) / 2
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(qx - 2.2 * mm, qy - 2.2 * mm, qr_size + 4.4 * mm, qr_size + 4.4 * mm, 4 * mm, stroke=0, fill=1)
    c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask='auto')

    text_x = qx + qr_size + 6.5 * mm
    text_w = max(22 * mm, footer_x + footer_w - text_x - 4 * mm)
    c.setFillColorRGB(1, 1, 1)
    qr_title = "Scan to view full menu" if lang == 'en' else 'Skann for å se hele menyen'
    qr_title_lines = _wrap_lines(qr_title, text_w, "Helvetica-Bold", 9.2)[:2]
    c.setFont("Helvetica-Bold", 9.2)
    title_y = footer_y + 23.8 * mm
    for line in qr_title_lines:
        c.drawString(text_x, title_y, line)
        title_y -= 4.1 * mm
    c.setFillColorRGB(*soft_text)
    c.setFont("Helvetica", 8.8)
    footer_lines = _wrap_lines(contact_line, text_w, "Helvetica", 8.8)[:2]
    fy = footer_y + 12.2 * mm
    for line in footer_lines:
        c.drawString(text_x, fy, line)
        fy -= 4.0 * mm

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf

def _make_flyer_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    colors = _brand_colors(str(listing.get("plan") or "standard"))
    page_margin = 12 * mm
    url = _public_listing_url(request, listing.get("slug") or "")
    title = str(listing.get("name") or "Kitchen").strip()
    subtitle = f"{listing.get('area','')} · {listing.get('city','')}".strip(" ·")
    tagline = _flyer_support_text(listing, lang)
    sig_title, sig_desc, _sig_price_unused = _get_signature_dish(listing, lang)
    contact_line = _safe_contact_line(listing)
    hero_img = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    flyer_accent = _hex_to_rgb01(listing.get("flyer_accent") or "#8557c7")
    flyer_accent_soft = tuple(min(1.0, (v * 0.22) + 0.78) for v in flyer_accent)
    flyer_img_focal_x = float(listing.get("flyer_image_focal_x") or 50)
    flyer_img_focal_y = float(listing.get("flyer_image_focal_y") or 50)
    flyer_img_zoom = float(listing.get("flyer_image_zoom") or 100)
    sig_img = _signature_image_path(listing)

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = None

    c.setFillColorRGB(0.97, 0.96, 0.94)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Artboard
    art_x = page_margin
    art_y = page_margin
    art_w = W - (2 * page_margin)
    art_h = H - (2 * page_margin)

    # Left hero image area
    image_w = art_w * 0.62
    image_h = art_h
    image_x = art_x
    image_y = art_y
    drew_hero = _draw_cover_photo_adjusted(c, hero_img, image_x, image_y, image_w, image_h, focal_x=flyer_img_focal_x, focal_y=flyer_img_focal_y, zoom=flyer_img_zoom)
    if not drew_hero:
        c.setFillColorRGB(*flyer_accent_soft)
        c.rect(image_x, image_y, image_w, image_h, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFillAlpha(0.14)
    c.rect(image_x, image_y, image_w, image_h, stroke=0, fill=1)
    c.setFillAlpha(1)

    # Diagonal accent overlay to make the flyer feel more commercial/editorial
    panel_overlap = 14 * mm
    panel_x = image_x + image_w - panel_overlap
    panel_w = art_x + art_w - panel_x
    panel_y = art_y
    panel_h = art_h

    c.setFillColorRGB(0.985, 0.975, 0.96)
    c.roundRect(panel_x, panel_y, panel_w, panel_h, 0, stroke=0, fill=1)

    wedge = c.beginPath()
    wedge.moveTo(panel_x, panel_y)
    wedge.lineTo(panel_x, panel_y + panel_h)
    wedge.lineTo(panel_x - 26 * mm, panel_y + panel_h)
    wedge.lineTo(panel_x - 5 * mm, panel_y)
    wedge.close()
    flyer_violet = flyer_accent
    flyer_violet_light = flyer_accent_soft
    c.setFillColorRGB(*flyer_violet)
    c.setFillAlpha(0.70)
    c.drawPath(wedge, stroke=0, fill=1)
    c.setFillAlpha(1)

    # Image text block
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(image_x + 9 * mm, image_y + image_h - 16 * mm, (title[:28]).upper())
    if subtitle:
        c.setFont("Helvetica", 10.8)
        c.drawString(image_x + 9 * mm, image_y + image_h - 22 * mm, subtitle[:34])

    # Signature dish tile inside image area
    tile_w = 52 * mm
    tile_h = 48 * mm
    tile_x = image_x + 9 * mm
    tile_y = image_y + 11 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setFillAlpha(0.98)
    c.roundRect(tile_x, tile_y, tile_w, tile_h, 3 * mm, stroke=0, fill=1)
    c.setFillAlpha(1)
    inner_img_h = 25 * mm
    if _draw_cover_photo(c, sig_img, tile_x + 3 * mm, tile_y + tile_h - inner_img_h - 3 * mm, tile_w - 6 * mm, inner_img_h):
        pass
    else:
        c.setFillColorRGB(*flyer_violet_light)
        c.roundRect(tile_x + 3 * mm, tile_y + tile_h - inner_img_h - 3 * mm, tile_w - 6 * mm, inner_img_h, 2 * mm, stroke=0, fill=1)
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica-Bold", 7.3)
    c.drawString(tile_x + 4 * mm, tile_y + 16 * mm, "SIGNATURE DISH" if lang == "en" else "SIGNATURRETT")
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(tile_x + 4 * mm, tile_y + 11 * mm, (sig_title or ("Fresh homemade menu" if lang == "en" else "Fersk hjemmelaget meny"))[:23])
    c.setFillColorRGB(*colors["muted"])
    c.setFont("Helvetica", 7.4)
    desc_line = (sig_desc or ("Made with care and ready to order." if lang == "en" else "Laget med omtanke og klar til bestilling.")).strip()
    for i, line in enumerate(_wrap_lines(desc_line, tile_w - 8 * mm, "Helvetica", 7.4)[:2]):
        c.drawString(tile_x + 4 * mm, tile_y + 6.2 * mm - i * 3.6 * mm, line)

    # Right editorial panel content
    inner_x = panel_x + 12 * mm
    inner_right = art_x + art_w - 10 * mm
    inner_w = inner_right - inner_x
    top_y = art_y + art_h - 15 * mm

    # Small label
    _draw_badge(c, inner_x, top_y - 1 * mm, "LOCAL ASIAN KITCHEN" if lang == "en" else "LOKALT ASIATISK KJØKKEN", flyer_violet, font_size=9.1, h=8.4 * mm, pad_x=4.1 * mm)

    # Kitchen name + headline
    c.setFillColorRGB(*flyer_violet)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inner_x, top_y - 12 * mm, title[:26])
    headline_lines = _flyer_headline_lines(listing, lang)
    # Keep the headline in the editorial panel, but make it feel more like a
    # clean ad headline: uppercase, slightly larger, with more breathing room
    # between the lines.
    headline_x = inner_x
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica-Bold", 20.5)
    hy = top_y - 26 * mm
    line_gap = 10.0 * mm
    for i, line in enumerate(headline_lines):
        c.drawString(headline_x, hy - i * line_gap, line)

    # Support copy
    support = tagline or ("Discover the menu, see the dishes and order in seconds." if lang == "en" else "Oppdag menyen, se rettene og bestill på få sekunder.")
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica", 16.2)
    sy = top_y - 58 * mm
    for line in _wrap_lines(support, inner_w - 4 * mm, "Helvetica", 16.2)[:3]:
        c.drawString(inner_x, sy, line)
        sy -= 6.3 * mm

    # QR call-to-action and code in a clean right-column zone (no box)
    qr_zone_x = inner_x
    qr_zone_y = art_y + 24 * mm
    qr_zone_w = inner_w
    qr_size = 41 * mm
    c.setFillColorRGB(*flyer_violet)
    c.setFont("Helvetica-Bold", 13.2)
    qr_head = ["SCAN TO VIEW MENU"] if lang == "en" else ["SKANN FOR Å SE MENY"]
    c.drawCentredString(qr_zone_x + (qr_zone_w / 2), qr_zone_y + qr_size + 8.2 * mm, qr_head[0])

    qx = qr_zone_x + (qr_zone_w - qr_size) / 2
    qy = qr_zone_y
    c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask="auto")

    # Contact line in same badge style as the category label, centered under QR
    contact_y = art_y + 8.6 * mm
    contact_label = "CONTACT" if lang == "en" else "KONTAKT"
    badge_fill = flyer_violet
    contact_text = f"{contact_label}  {contact_line[:30]}" if contact_line else url.replace("https://", "").replace("http://", "")[:30]
    contact_font = "Helvetica"
    contact_fs = 10.8
    contact_pad_x = 4.2 * mm
    contact_h = 8.6 * mm
    contact_tw = c.stringWidth(contact_text, contact_font, contact_fs)
    contact_box_w = contact_tw + 2 * contact_pad_x
    contact_box_x = inner_x + (inner_w - contact_box_w) / 2
    contact_box_y = contact_y - 3.6 * mm
    c.setFillColorRGB(*badge_fill)
    c.roundRect(contact_box_x, contact_box_y, contact_box_w, contact_h, 3.6 * mm, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(contact_font, contact_fs)
    c.drawCentredString(contact_box_x + (contact_box_w / 2), contact_box_y + 2.55 * mm, contact_text)

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _make_flyer2_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    title = str(listing.get("name") or ("Kitchen" if lang == "en" else "Kjøkken"))
    url = _public_listing_url(request, listing.get("slug") or "")
    contact_line = _safe_contact_line(listing)
    hero_img = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    sig_img = _signature_image_path(listing)
    sig_title, sig_desc, _ = _get_signature_dish(listing, lang)
    headline = " ".join(_flyer_headline_lines(listing, lang)).strip()
    support = _flyer_support_text(listing, lang) or ("Discover the menu, scan the QR and order in seconds." if lang == "en" else "Se menyen, skann QR-koden og bestill på få sekunder.")
    accent = _hex_to_rgb01(listing.get("flyer_accent") or "#8557c7")
    accent_soft = tuple(min(1.0, (v * 0.18) + 0.82) for v in accent)
    flyer_img_focal_x = float(listing.get("flyer_image_focal_x") or 50)
    flyer_img_focal_y = float(listing.get("flyer_image_focal_y") or 50)
    flyer_img_zoom = float(listing.get("flyer_image_zoom") or 100)
    ink_color = "#161616"
    bg_color = "#f7f1e8"

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")

    c.setFillColorRGB(0.97, 0.96, 0.94)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    page_margin = 11 * mm
    art_x = page_margin
    art_y = page_margin
    art_w = W - (2 * page_margin)
    art_h = H - (2 * page_margin)

    c.setFillColorRGB(1, 1, 1)
    c.roundRect(art_x, art_y, art_w, art_h, 7 * mm, stroke=0, fill=1)

    top_h = art_h * 0.44
    drew_hero = _draw_cover_photo_adjusted(c, hero_img, art_x, art_y + art_h - top_h, art_w, top_h, focal_x=flyer_img_focal_x, focal_y=flyer_img_focal_y, zoom=flyer_img_zoom)
    if not drew_hero:
        c.setFillColorRGB(*accent_soft)
        c.roundRect(art_x, art_y + art_h - top_h, art_w, top_h, 7 * mm, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFillAlpha(0.18)
    c.roundRect(art_x, art_y + art_h - top_h, art_w, top_h, 7 * mm, stroke=0, fill=1)
    c.setFillAlpha(1)

    dark = (0.08, 0.10, 0.14)
    bottom_h = art_h * 0.60
    bottom_y = art_y
    c.setFillColorRGB(*dark)
    c.roundRect(art_x, bottom_y, art_w, bottom_h, 10 * mm, stroke=0, fill=1)

    circle_d = 41 * mm
    circle_x = art_x + art_w - circle_d - 12 * mm
    circle_y = art_y + art_h - top_h - (circle_d * 0.52)
    c.setFillColorRGB(1, 1, 1)
    c.circle(circle_x + circle_d/2, circle_y + circle_d/2, circle_d/2 + 2.2 * mm, stroke=0, fill=1)
    c.saveState()
    p = c.beginPath()
    p.circle(circle_x + circle_d/2, circle_y + circle_d/2, circle_d/2)
    c.clipPath(p, stroke=0, fill=0)
    if not _draw_cover_photo(c, sig_img, circle_x, circle_y, circle_d, circle_d):
        c.setFillColorRGB(*accent_soft)
        c.circle(circle_x + circle_d/2, circle_y + circle_d/2, circle_d/2, stroke=0, fill=1)
    c.restoreState()

    text_x = art_x + 11 * mm
    text_top = art_y + bottom_h - 18 * mm
    c.setFillColorRGB(*accent)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(text_x, text_top, title[:34].upper())
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 27)
    headline_lines = _wrap_lines(headline, art_w - 30 * mm, "Helvetica-Bold", 27)[:3]
    hy = text_top - 12 * mm
    for i, line in enumerate(headline_lines):
        c.drawString(text_x, hy - i * 10.5 * mm, line)
    c.setFillColorRGB(*accent)
    c.roundRect(text_x, hy - len(headline_lines)*10.5*mm - 2*mm, 20 * mm, 1.9 * mm, 1 * mm, stroke=0, fill=1)

    support_y = hy - len(headline_lines) * 10.5 * mm - 10 * mm
    c.setFillColorRGB(0.86, 0.88, 0.92)
    c.setFont("Helvetica", 11.8)
    for i, line in enumerate(_wrap_lines(support, art_w * 0.54, "Helvetica", 11.8)[:4]):
        c.drawString(text_x, support_y - i * 5.0 * mm, line)

    sig_block_x = circle_x - 4 * mm
    sig_block_y = art_y + 55 * mm
    c.setFillColorRGB(*accent)
    c.setFont("Helvetica-Bold", 9.4)
    c.drawString(sig_block_x, sig_block_y + 12 * mm, "SIGNATURE DISH" if lang == "en" else "SIGNATURRETT")
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 15)
    for i, line in enumerate(_wrap_lines(sig_title or ("Signature dish" if lang == "en" else "Signaturrett"), 54 * mm, "Helvetica-Bold", 15)[:2]):
        c.drawString(sig_block_x, sig_block_y + 6 * mm - i * 6 * mm, line)
    c.setFillColorRGB(0.80, 0.83, 0.88)
    c.setFont("Helvetica", 9.4)
    for i, line in enumerate(_wrap_lines(sig_desc or ("Made with care and ready to order." if lang == "en" else "Laget med omtanke og klar til bestilling."), 54 * mm, "Helvetica", 9.4)[:3]):
        c.drawString(sig_block_x, sig_block_y - 3 * mm - i * 4.1 * mm, line)

    footer_x = art_x + 10 * mm
    footer_y = art_y + 10 * mm
    footer_w = art_w - 20 * mm
    footer_h = 28 * mm
    c.setFillColorRGB(0.12, 0.15, 0.21)
    c.roundRect(footer_x, footer_y, footer_w, footer_h, 5 * mm, stroke=0, fill=1)
    q_size = 19 * mm
    qx = footer_x + footer_w - q_size - 5 * mm
    qy = footer_y + (footer_h - q_size) / 2
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(qx - 2 * mm, qy - 2 * mm, q_size + 4 * mm, q_size + 4 * mm, 3 * mm, stroke=0, fill=1)
    c.drawImage(ImageReader(qr_img), qx, qy, width=q_size, height=q_size, mask="auto")
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10.8)
    c.drawString(footer_x + 5 * mm, footer_y + 17 * mm, "SCAN TO VIEW MENU" if lang == "en" else "SKANN FOR Å SE MENY")
    c.setFillColorRGB(0.83, 0.86, 0.90)
    c.setFont("Helvetica", 9.4)
    footer_text = contact_line or url.replace("https://", "").replace("http://", "")
    for i, line in enumerate(_wrap_lines(footer_text, footer_w - q_size - 18 * mm, "Helvetica", 9.4)[:2]):
        c.drawString(footer_x + 5 * mm, footer_y + 11 * mm - i * 4.2 * mm, line)

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _get_business_card_settings(listing: dict, request: Request):
    colors = _brand_colors(str(listing.get("plan") or "standard"))
    qp = getattr(request, "query_params", {}) or {}
    try:
        hero_focal_x = float(qp.get("hero_focal_x", listing.get("business_card_image_focal_x", 50)) or 50)
    except Exception:
        hero_focal_x = 50.0
    try:
        hero_focal_y = float(qp.get("hero_focal_y", listing.get("business_card_image_focal_y", 50)) or 50)
    except Exception:
        hero_focal_y = 50.0
    try:
        hero_zoom = float(qp.get("hero_zoom", listing.get("business_card_image_zoom", 100)) or 100)
    except Exception:
        hero_zoom = 100.0
    try:
        name_font_size = float(qp.get("name_font_size", listing.get("business_card_name_font_size", 12.4)) or 12.4)
    except Exception:
        name_font_size = 12.4
    name_color_raw = str(qp.get("name_color", listing.get("business_card_name_color") or "") or "").strip()
    brand_color_raw = str(qp.get("brand_color", listing.get("business_card_brand_color") or "") or "").strip()
    bg1_color_raw = str(qp.get("bg1_color", listing.get("business_card_bg_color_1") or "") or "").strip()
    bg_color_raw = str(qp.get("bg_color", listing.get("business_card_bg_color") or "") or "").strip()
    location_color_raw = str(qp.get("location_color", listing.get("business_card_location_color") or "") or "").strip()
    phone_color_raw = str(qp.get("phone_color", listing.get("business_card_phone_color") or "") or "").strip()
    style_raw = str(qp.get("style", listing.get("business_card_style") or "1") or "1").strip().lower()
    style = "2" if style_raw in {"2", "minimal", "elegant-minimal", "elegant_minimal", "brand-line", "brand_line"} else "1"
    hero_focal_x = max(0.0, min(100.0, hero_focal_x))
    hero_focal_y = max(0.0, min(100.0, hero_focal_y))
    hero_zoom = max(100.0, min(200.0, hero_zoom))
    name_font_size = max(8.0, min(18.0, name_font_size))
    name_color = _hex_to_rgb01(name_color_raw, fallback=colors["ink"]) if re.fullmatch(r"#[0-9a-fA-F]{6}", name_color_raw or "") else colors["ink"]
    brand_color = _hex_to_rgb01(brand_color_raw, fallback=(0.41, 0.27, 0.23)) if re.fullmatch(r"#[0-9a-fA-F]{6}", brand_color_raw or "") else (0.41, 0.27, 0.23)
    bg1_color = _hex_to_rgb01(bg1_color_raw, fallback=(0.952, 0.922, 0.875)) if re.fullmatch(r"#[0-9a-fA-F]{6}", bg1_color_raw or "") else (0.952, 0.922, 0.875)
    bg_color = _hex_to_rgb01(bg_color_raw, fallback=(0.72, 0.66, 0.60)) if re.fullmatch(r"#[0-9a-fA-F]{6}", bg_color_raw or "") else (0.72, 0.66, 0.60)
    location_color = _hex_to_rgb01(location_color_raw, fallback=colors["muted"]) if re.fullmatch(r"#[0-9a-fA-F]{6}", location_color_raw or "") else colors["muted"]
    phone_color = _hex_to_rgb01(phone_color_raw, fallback=colors["muted"]) if re.fullmatch(r"#[0-9a-fA-F]{6}", phone_color_raw or "") else colors["muted"]
    return {
        "colors": colors,
        "hero_focal_x": hero_focal_x,
        "hero_focal_y": hero_focal_y,
        "hero_zoom": hero_zoom,
        "name_font_size": name_font_size,
        "name_color": name_color,
        "brand_color": brand_color,
        "bg1_color": bg1_color,
        "bg_color": bg_color,
        "location_color": location_color,
        "phone_color": phone_color,
        "style": style,
    }



def _draw_business_card_style_1(c, listing: dict, request: Request, lang: str, x: float, y: float, card_w: float, card_h: float, s: dict):
    colors = s["colors"]
    url = _public_listing_url(request, listing.get("slug") or "")
    name = str(listing.get("name") or "Kitchen").strip()
    area = str(listing.get("area") or "").strip()
    city = str(listing.get("city") or "").strip()
    place_line = f"{area} · {city}".strip(" ·") or city or area
    contact = listing.get("contact") or {}
    phone = str((contact.get("phone") or contact.get("whatsapp") or listing.get("phone") or "")).strip()
    photo = _resolve_public_image_path(str(listing.get("hero_image") or "")) or _signature_image_path(listing)

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=1)
    qr.add_data(url)
    qr.make(fit=True)

    cream = s.get("bg1_color") or (0.952, 0.922, 0.875)
    contact_color = s.get("phone_color") or s.get("location_color") or colors["muted"]
    qr_img = qr.make_image(fill_color=_rgb01_to_hex(contact_color), back_color=_rgb01_to_hex(cream)).convert("RGB")

    c.setFillColorRGB(1, 1, 1)
    c.rect(x, y, card_w, card_h, stroke=0, fill=1)

    hero_h = card_h * 0.52
    hero_y = y + card_h - hero_h
    body_y = y
    body_h = card_h - hero_h

    if not _draw_cover_photo_adjusted(c, photo, x, hero_y, card_w, hero_h, focal_x=s["hero_focal_x"], focal_y=s["hero_focal_y"], zoom=s["hero_zoom"]):
        c.setFillColorRGB(*colors["accent2"])
        c.rect(x, hero_y, card_w, hero_h, stroke=0, fill=1)

    c.setFillColorRGB(*cream)
    c.rect(x, body_y, card_w, body_h, stroke=0, fill=1)

    pad = 4.6 * mm
    left_x = x + pad
    right_x = x + card_w - pad

    qr_size = 20 * mm
    qr_outer = qr_size + 4 * mm
    qr_x = right_x - qr_size
    qr_y = hero_y - (qr_size * 0.75)
    qr_outer_x = qr_x - 2 * mm
    qr_outer_y = qr_y - 2 * mm

    c.drawImage(ImageReader(qr_img), qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")

    name_y = hero_y - 9.0 * mm
    text_right = qr_x - 4.5 * mm
    text_w = max(20, text_right - left_x)

    c.setFillColorRGB(*s["name_color"])
    name_font = s["name_font_size"]
    c.setFont("Times-BoldItalic", name_font)
    display_name = name
    while display_name and c.stringWidth(display_name, "Times-BoldItalic", name_font) > text_w:
        display_name = display_name[:-2].rstrip()
    if display_name != name:
        display_name = (display_name.rstrip('. ') + '…').strip()
    c.drawString(left_x, name_y, display_name)

    meta_y = name_y - 6.8 * mm
    c.setFont("Helvetica", 8.2)
    if place_line:
        c.setFillColorRGB(*(s.get("location_color") or colors["muted"]))
        c.drawString(left_x, meta_y, place_line[:34])
        meta_y -= 4.2 * mm
    if phone:
        c.setFillColorRGB(*(s.get("phone_color") or colors["muted"]))
        c.drawString(left_x, meta_y, phone[:28])

    c.setFillColorRGB(*contact_color)
    c.setFont("Helvetica", 8.6)
    scan_text = "Scan menu" if lang == "en" else "Skann meny"
    scan_w = c.stringWidth(scan_text, "Helvetica", 8.6)
    c.drawString(qr_x + (qr_size - scan_w) / 2, qr_y - 4.2 * mm, scan_text)




def _draw_business_card_style_2(c, listing: dict, request: Request, lang: str, x: float, y: float, card_w: float, card_h: float, s: dict):
    url = _public_listing_url(request, listing.get("slug") or "")
    name = str(listing.get("name") or "Kitchen").strip()
    area = str(listing.get("area") or "").strip()
    city = str(listing.get("city") or "").strip()
    place_line = f"{area} · {city}".strip(" ·") or city or area
    contact = listing.get("contact") or {}
    phone = str((contact.get("phone") or contact.get("whatsapp") or listing.get("phone") or "")).strip()

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=1)
    qr.add_data(url)
    qr.make(fit=True)

    brand_color = s.get("brand_color") or (0.41, 0.27, 0.23)

    # darker, more distinct paper tone than style 1
    paper = s.get("bg_color") or (0.72, 0.66, 0.60)
    qr_img = qr.make_image(fill_color=_rgb01_to_hex(brand_color), back_color=_rgb01_to_hex(paper)).convert("RGB")
    muted = (0.27, 0.22, 0.19)
    brand = "Fresh Asian Taste"

    c.setFillColorRGB(*paper)
    c.rect(x, y, card_w, card_h, stroke=0, fill=1)

    # --- QR lower on the right: top edge aligned to the rule ---
    qr_size = 17.2 * mm
    line_y = y + 21.5 * mm
    qr_x = x + card_w - 23.2 * mm
    qr_y = line_y - qr_size
    c.drawImage(ImageReader(qr_img), qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")

    # --- Brand line: slightly higher than before ---
    cx = x + card_w * 0.50
    top_y = y + card_h - 14.8 * mm

    c.setFillColorRGB(*brand_color)
    c.setFont("Times-Italic", 20.0)
    fresh = "Fresh Asian"
    fresh_w = c.stringWidth(fresh, "Times-Italic", 20.0)
    c.drawString(cx - fresh_w / 2, top_y, fresh)

    c.setFont("Times-BoldItalic", 29.0)
    taste = "Taste"
    taste_w = c.stringWidth(taste, "Times-BoldItalic", 29.0)
    taste_x = cx - taste_w / 2
    taste_y = top_y - 8.4 * mm
    c.drawString(taste_x, taste_y, taste)

    # Decorative flourishes to create a much more swirled expression without custom fonts
    c.setStrokeColorRGB(*brand_color)
    c.setLineWidth(0.7)
    left_start = taste_x - 9.5 * mm
    left_end = taste_x - 0.8 * mm
    y_mid = taste_y + 2.2 * mm
    p = c.beginPath()
    p.moveTo(left_end, y_mid)
    p.curveTo(left_start + 8 * mm, y_mid + 5 * mm, left_start + 2 * mm, y_mid + 5 * mm, left_start + 3 * mm, y_mid + 1.2 * mm)
    p.curveTo(left_start + 4 * mm, y_mid - 2.8 * mm, left_start + 10 * mm, y_mid - 3.0 * mm, left_start + 8 * mm, y_mid + 0.8 * mm)
    p.curveTo(left_start + 7 * mm, y_mid + 3.6 * mm, left_start + 1 * mm, y_mid + 2.8 * mm, left_start + 1.8 * mm, y_mid - 0.8 * mm)
    c.drawPath(p, stroke=1, fill=0)

    right_start = taste_x + taste_w + 0.8 * mm
    right_end = right_start + 9.5 * mm
    p = c.beginPath()
    p.moveTo(right_start, y_mid)
    p.curveTo(right_start + 4 * mm, y_mid + 5 * mm, right_end - 5 * mm, y_mid + 5 * mm, right_end - 3 * mm, y_mid + 1.0 * mm)
    p.curveTo(right_end - 2 * mm, y_mid - 2.8 * mm, right_end - 8 * mm, y_mid - 3.2 * mm, right_end - 7 * mm, y_mid + 0.8 * mm)
    p.curveTo(right_end - 6 * mm, y_mid + 3.8 * mm, right_end + 0.5 * mm, y_mid + 2.8 * mm, right_end - 0.2 * mm, y_mid - 1.0 * mm)
    c.drawPath(p, stroke=1, fill=0)

    # --- rule and left-aligned info below center ---
    line_left = x + 7.0 * mm
    line_right = qr_x - 3.0 * mm
    c.setStrokeColorRGB(*brand_color)
    c.setLineWidth(0.42 * mm)
    c.line(line_left, line_y, line_right, line_y)

    info_left_x = x + 7.0 * mm
    text_w = max(22 * mm, line_right - info_left_x)
    c.setFillColorRGB(*s["name_color"])
    name_font = min(12.8, max(10.2, s["name_font_size"] + 1.0))
    c.setFont("Helvetica-Bold", name_font)
    display_name = name
    while display_name and c.stringWidth(display_name, "Helvetica-Bold", name_font) > text_w:
        display_name = display_name[:-2].rstrip()
    if display_name != name:
        display_name = (display_name.rstrip('. ') + '…').strip()
    name_y = y + 15.6 * mm
    c.drawString(info_left_x, name_y, display_name)

    c.setFont("Helvetica", 8.8)
    meta_y = name_y - 5.2 * mm
    if place_line:
        c.setFillColorRGB(*(s.get("location_color") or muted))
        c.drawString(info_left_x, meta_y, place_line[:34])
        meta_y -= 4.0 * mm
    if phone:
        c.setFillColorRGB(*(s.get("phone_color") or muted))
        c.drawString(info_left_x, meta_y, phone[:28])


def _draw_business_card(c, listing: dict, request: Request, lang: str, x: float, y: float, card_w: float, card_h: float):
    s = _get_business_card_settings(listing, request)
    if s["style"] == "2":
        _draw_business_card_style_2(c, listing, request, lang, x, y, card_w, card_h, s)
    else:
        _draw_business_card_style_1(c, listing, request, lang, x, y, card_w, card_h, s)



def _get_thank_you_card_settings(listing: dict, request: Request):
    qp = request.query_params
    variant_raw = str(qp.get("variant", listing.get("thank_you_card_variant") or "1") or "1").strip()
    if variant_raw not in ("1", "2", "3", "4", "5"):
        variant_raw = "1"

    def _pick_hex(query_key: str, listing_key: str, default: str) -> str:
        raw = str(qp.get(query_key, listing.get(listing_key) or default) or default).strip()
        return raw if re.fullmatch(r'#[0-9a-fA-F]{6}', raw or '') else default

    def _pick_pct(query_key: str, listing_key: str, default: float, min_value: float, max_value: float) -> float:
        try:
            raw = float(qp.get(query_key, listing.get(listing_key) if listing.get(listing_key) is not None else default))
        except Exception:
            raw = float(default)
        return max(min_value, min(max_value, raw))

    return {
        "variant": variant_raw,
        "bg_color": _pick_hex("bg_color", "thank_you_card_bg_color", "#e2227f" if variant_raw == "5" else "#9b1c53"),
        "title_color": _pick_hex("title_color", "thank_you_card_title_color", "#ffffff" if variant_raw == "5" else "#ffffff"),
        "name_color": _pick_hex("name_color", "thank_you_card_name_color", "#ffffff" if variant_raw == "5" else "#000000"),
        "image_focal_x": _pick_pct("image_focal_x", "thank_you_card_image_focal_x", 50.0, 0.0, 100.0),
        "image_focal_y": _pick_pct("image_focal_y", "thank_you_card_image_focal_y", 50.0, 0.0, 100.0),
        "image_zoom": _pick_pct("image_zoom", "thank_you_card_image_zoom", 100.0, 0.0, 200.0),
        "heart_scale": _pick_pct("heart_scale", "thank_you_card_heart_scale", 100.0, 30.0, 180.0),
        "heart_x": _pick_pct("heart_x", "thank_you_card_heart_x", 47.0, -20.0, 90.0),
        "heart_y": _pick_pct("heart_y", "thank_you_card_heart_y", -4.9, -30.0, 30.0),
        "heart_rotation": _pick_pct("heart_rotation", "thank_you_card_heart_rotation", -4.0, -180.0, 180.0),
    }


def _thank_you_card_copy(lang: str, variant: str):
    en = {
        "1": ("Thank you for your order", "Hope you enjoy your meal.", "Welcome again"),
        "2": ("Hope you enjoy your meal", "Thank you for supporting us.", "Welcome again"),
        "3": ("Made with care", "We hope it tastes great.", "See you again soon"),
        "4": ("Thank you", "Fresh homemade food, made for you.", "Welcome back anytime"),
        "5": ("Thank you", "For your order", ""),
    }
    no = {
        "1": ("Takk for bestillingen", "Håper maten smaker.", "Velkommen igjen"),
        "2": ("Håper maten smaker", "Takk for at du støtter kjøkkenet vårt.", "Velkommen igjen"),
        "3": ("Laget med omtanke", "Vi håper det smaker godt.", "Vi sees igjen snart"),
        "4": ("Takk", "Fersk hjemmelaget mat, laget for deg.", "Velkommen tilbake når som helst"),
        "5": ("Takk", "For bestillingen", ""),
    }
    return (no if (lang or 'en') == 'no' else en).get(variant or '1', en['1'])


def _draw_thank_you_card_style_5(c, listing: dict, request: Request, lang: str, x: float, y: float, card_w: float, card_h: float, s: dict):
    title, line1, _line2 = _thank_you_card_copy(lang, s['variant'])
    if (lang or 'en') == 'en' and title == 'Thank you for your order':
        title = 'Thank you'
    name = str(listing.get('name') or 'Kitchen').strip() or 'Kitchen'

    bg_rgb = _hex_to_rgb01(s.get('bg_color') or '#e2227f', fallback=(0.886, 0.133, 0.498))
    title_rgb = _hex_to_rgb01(s.get('title_color') or '#ffffff', fallback=(1.0, 1.0, 1.0))
    name_rgb = _hex_to_rgb01(s.get('name_color') or '#ffffff', fallback=(1.0, 1.0, 1.0))
    speck_rgb = tuple(max(0.0, min(1.0, c * 0.85)) for c in bg_rgb)

    c.setFillColorRGB(*bg_rgb)
    c.rect(x, y, card_w, card_h, stroke=0, fill=1)

    # subtle paper speckles so the card feels a little less flat
    c.setFillColorRGB(*speck_rgb)
    for idx in range(44):
        px = x + 4 * mm + ((idx * 23) % int(max(10, card_w - 8 * mm)))
        py = y + 4 * mm + ((idx * 37) % int(max(10, card_h - 8 * mm)))
        r = 0.18 * mm if idx % 3 else 0.24 * mm
        c.circle(px, py, r, stroke=0, fill=1)

    # large hand-written inspired title
    c.saveState()
    c.setFillColorRGB(*title_rgb)
    c.translate(x + 15.5 * mm, y + card_h - 19.0 * mm)
    c.rotate(9)
    title_font = 'Times-BoldItalic'
    title_size = 39 if len(title) <= 9 else 34
    lines = title.split(' ', 1) if ' ' in title else [title]
    if len(lines) == 1:
        lines = [title, '']
    c.setFont(title_font, title_size)
    c.drawString(0, 0, lines[0])
    if lines[1]:
        c.drawString(12 * mm, -11.5 * mm, lines[1])
    # adjustable heart for style 5: size, offset, and rotation can be edited in Tools
    c.saveState()
    hx = min(card_w - 18 * mm, float(s.get('heart_x', 47.0)) * mm)
    hy = float(s.get('heart_y', -4.9)) * mm
    hscale = float(s.get('heart_scale', 72.0)) / 100.0
    hrot = float(s.get('heart_rotation', 0.0))
    c.translate(hx, hy)
    if abs(hrot) > 0.01:
        c.rotate(hrot)
    c.scale(hscale, hscale)
    heart = c.beginPath()
    heart.moveTo(0, -6.8 * mm)
    heart.curveTo(-6.3 * mm, -1.8 * mm, -9.5 * mm, 3.2 * mm, -6.0 * mm, 7.7 * mm)
    heart.curveTo(-3.8 * mm, 10.4 * mm, -1.2 * mm, 8.3 * mm, 0, 6.3 * mm)
    heart.curveTo(1.2 * mm, 8.3 * mm, 3.8 * mm, 10.4 * mm, 6.0 * mm, 7.7 * mm)
    heart.curveTo(9.5 * mm, 3.2 * mm, 6.3 * mm, -1.8 * mm, 0, -6.8 * mm)
    c.setLineWidth(1.0)
    c.setStrokeColorRGB(*title_rgb)
    c.drawPath(heart, stroke=1, fill=0)
    c.restoreState()
    c.restoreState()

    c.setFillColorRGB(*title_rgb)
    c.setFont('Helvetica', 7.8)
    c.drawString(x + 51 * mm, y + 10.0 * mm, str(line1 or '').upper())

    c.setFillColorRGB(*name_rgb)
    c.setFont('Helvetica', 6.7)
    kitchen_line = name.upper()
    max_w = card_w - 12 * mm
    while kitchen_line and c.stringWidth(kitchen_line, 'Helvetica', 6.7) > max_w:
        kitchen_line = kitchen_line[:-1].rstrip()
    c.drawString(x + 6 * mm, y + 5.3 * mm, kitchen_line)


def _draw_thank_you_card(c, listing: dict, request: Request, lang: str, x: float, y: float, card_w: float, card_h: float):
    def _fit_lines(text: str, font_name: str, font_size: float, max_width: float, max_lines: int = 2):
        words = [w for w in str(text or '').split() if w]
        if not words:
            return ['']
        lines = []
        current = words[0]
        for word in words[1:]:
            test = f"{current} {word}".strip()
            if c.stringWidth(test, font_name, font_size) <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
        if len(lines) <= max_lines:
            return lines
        kept = lines[:max_lines]
        overflow = ' '.join(lines[max_lines - 1:])
        trimmed = kept[-1]
        while overflow and c.stringWidth(trimmed + '…', font_name, font_size) > max_width and len(trimmed) > 1:
            trimmed = trimmed[:-1].rstrip()
        kept[-1] = (trimmed.rstrip('. ') + '…').strip()
        return kept

    def _trim_to_width(text: str, font_name: str, font_size: float, max_width: float):
        text = str(text or '').strip()
        if not text:
            return ''
        if c.stringWidth(text, font_name, font_size) <= max_width:
            return text
        trimmed = text
        while trimmed and c.stringWidth(trimmed + '…', font_name, font_size) > max_width:
            trimmed = trimmed[:-1].rstrip()
        return (trimmed.rstrip('. ') + '…').strip() if trimmed else ''

    s = _get_thank_you_card_settings(listing, request)
    if s.get('variant') == '5':
        _draw_thank_you_card_style_5(c, listing, request, lang, x, y, card_w, card_h, s)
        return
    title, line1, line2 = _thank_you_card_copy(lang, s['variant'])
    if (lang or 'en') == 'en' and title == 'Thank you for your order':
        title = 'Thank you'
    name = str(listing.get('name') or 'Kitchen').strip() or 'Kitchen'
    contact = listing.get('contact') or {}
    phone = str((contact.get('phone') or contact.get('whatsapp') or listing.get('phone') or '')).strip()
    url = _public_listing_url(request, listing.get('slug') or '')
    hero = _resolve_public_image_path(str(listing.get('hero_image') or '')) or _signature_image_path(listing)

    bg_raw = s['bg_color']
    title_raw = s['title_color']
    name_raw = s['name_color']
    bg_rgb = _hex_to_rgb01(bg_raw, fallback=(0.918, 0.816, 0.741))
    ink = _hex_to_rgb01('#3a2418')
    name_rgb = _hex_to_rgb01(name_raw, fallback=(0.227, 0.141, 0.094))
    soft = _hex_to_rgb01('#f8efe7')
    accent = _hex_to_rgb01(title_raw, fallback=(0.604, 0.337, 0.212))

    c.setFillColorRGB(*bg_rgb)
    c.rect(x, y, card_w, card_h, stroke=0, fill=1)

    image_d = 21.5 * mm
    image_x = x + 6.0 * mm
    image_y = y + card_h - image_d - 6.5 * mm
    image_cx = image_x + image_d / 2
    image_cy = image_y + image_d / 2
    c.setFillColorRGB(*soft)
    c.circle(image_cx, image_cy, (image_d / 2) + 1.1 * mm, stroke=0, fill=1)

    drew_circle = False
    if hero and os.path.exists(hero):
        try:
            with Image.open(hero) as img0:
                img = ImageOps.exif_transpose(img0).convert('RGBA')
                zoom_pct = max(0.0, min(200.0, float(s.get('image_zoom', 100.0) or 100.0)))
                zoom = max(1.0, zoom_pct / 100.0)
                base_side = max(1, min(img.width, img.height))
                fx = max(0.0, min(100.0, float(s.get('image_focal_x', 50.0) or 50.0))) / 100.0
                fy = max(0.0, min(100.0, float(s.get('image_focal_y', 50.0) or 50.0))) / 100.0
                center_x = int(round(fx * img.width))
                center_y = int(round(fy * img.height))
                if zoom_pct >= 100.0:
                    crop_side = max(1, int(round(base_side / zoom)))
                    crop_side = min(crop_side, img.width, img.height)
                    left = max(0, min(img.width - crop_side, center_x - crop_side // 2))
                    top = max(0, min(img.height - crop_side, center_y - crop_side // 2))
                    img = img.crop((left, top, left + crop_side, top + crop_side)).resize((700, 700), Image.LANCZOS)
                else:
                    crop_side = base_side
                    left = max(0, min(img.width - crop_side, center_x - crop_side // 2))
                    top = max(0, min(img.height - crop_side, center_y - crop_side // 2))
                    src = img.crop((left, top, left + crop_side, top + crop_side)).resize((700, 700), Image.LANCZOS)
                    canvas = Image.new('RGBA', (700, 700), (0, 0, 0, 0))
                    scaled_side = max(1, int(round(700 * max(0.0, zoom_pct) / 100.0)))
                    scaled = src.resize((scaled_side, scaled_side), Image.LANCZOS)
                    offset = ((700 - scaled_side) // 2, (700 - scaled_side) // 2)
                    canvas.alpha_composite(scaled, offset)
                    img = canvas
                mask = Image.new('L', (700, 700), 0)
                mdraw = ImageDraw.Draw(mask)
                mdraw.ellipse((0, 0, 699, 699), fill=255)
                out = Image.new('RGBA', (700, 700), (255, 255, 255, 0))
                out.paste(img, (0, 0), mask)
                buf = BytesIO()
                out.save(buf, format='PNG')
                buf.seek(0)
                c.drawImage(ImageReader(buf), image_x, image_y, width=image_d, height=image_d, mask='auto')
                drew_circle = True
        except Exception:
            drew_circle = False
    if not drew_circle:
        c.setFillColorRGB(0.87, 0.73, 0.62)
        c.circle(image_cx, image_cy, image_d / 2, stroke=0, fill=1)

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=0)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=title_raw, back_color=bg_raw).convert('RGB')
    qr_size = 11.2 * mm
    qx = x + card_w - qr_size - 5.6 * mm
    qy = y + 4.0 * mm
    c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask='auto')

    text_left = x + 33.5 * mm
    text_right = x + card_w - 8.0 * mm
    title_max_w = text_right - text_left
    title_font = 'Times-BoldItalic'
    title_size = 14.2
    title_lines = _fit_lines(title, title_font, title_size, title_max_w, max_lines=2)
    image_mid_y = image_y + (image_d / 2)
    title_step = 5.2 * mm
    title_center_y = image_mid_y - 2.0 * mm
    first_title_y = title_center_y + ((len(title_lines) - 1) * title_step / 2)
    c.setFillColorRGB(*accent)
    c.setFont(title_font, title_size)
    for i, ln in enumerate(title_lines):
        c.drawString(text_left, first_title_y - i * title_step, ln)

    body_left = text_left
    body_right = x + card_w - 18.5 * mm
    body_max_w = body_right - body_left
    body_y = y + card_h - 27.8 * mm
    line1_lines = _fit_lines(line1, 'Helvetica-Bold', 8.9, body_max_w, max_lines=2)
    line2_lines = _fit_lines(line2, 'Helvetica', 8.3, body_max_w, max_lines=2)

    c.setFillColorRGB(*ink)
    yy = body_y
    c.setFont('Helvetica-Bold', 8.9)
    for ln in line1_lines:
        c.drawString(body_left, yy, ln)
        yy -= 4.2 * mm
    yy -= 0.5 * mm
    c.setFillColorRGB(*accent)
    c.setFont('Helvetica', 8.3)
    for ln in line2_lines:
        c.drawString(body_left, yy, ln)
        yy -= 3.8 * mm

    line_y = y + 13.0 * mm
    line_left = x + 7.5 * mm
    line_right = x + card_w - 22.5 * mm
    c.setStrokeColorRGB(*accent)
    c.setLineWidth(0.8)
    c.line(line_left, line_y, line_right, line_y)

    c.setFillColorRGB(*name_rgb)
    name_font = 8.3
    meta_font = 7.7
    text_max_w = line_right - line_left
    display_name = _trim_to_width(name, 'Helvetica-Bold', name_font, text_max_w)
    display_phone = _trim_to_width(phone, 'Helvetica', meta_font, text_max_w) if phone else ''
    name_y = y + 8.9 * mm
    c.setFont('Helvetica-Bold', name_font)
    c.drawString(line_left, name_y, display_name)
    if display_phone:
        c.setFillColorRGB(*ink)
        c.setFont('Helvetica', meta_font)
        c.drawString(line_left, name_y - 3.6 * mm, display_phone)


def _make_thank_you_cards_pdf(listing: dict, request: Request, lang: str = 'en', layout: str = 'sheet') -> BytesIO:
    pdf = BytesIO()
    card_w = 85 * mm
    card_h = 55 * mm

    layout_mode = (layout or 'sheet').lower().strip()
    if layout_mode == 'single':
        c = canvas.Canvas(pdf, pagesize=(card_w, card_h))
        _draw_thank_you_card(c, listing, request, lang, 0, 0, card_w, card_h)
    else:
        page_size = landscape(A4)
        c = canvas.Canvas(pdf, pagesize=page_size)
        W, H = page_size
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        cols = 3
        rows = 3
        gap_x = 6 * mm
        gap_y = 6 * mm
        margin_x = (W - (cols * card_w + (cols - 1) * gap_x)) / 2
        margin_y = (H - (rows * card_h + (rows - 1) * gap_y)) / 2
        for row in range(rows):
            for col in range(cols):
                xx = margin_x + col * (card_w + gap_x)
                yy = H - margin_y - (row + 1) * card_h - row * gap_y
                _draw_thank_you_card(c, listing, request, lang, xx, yy, card_w, card_h)
    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _make_business_cards_pdf(listing: dict, request: Request, lang: str = "en", layout: str = "sheet") -> BytesIO:
    pdf = BytesIO()
    card_w = 85 * mm
    card_h = 55 * mm

    layout_mode = (layout or "sheet").lower().strip()
    if layout_mode == "single":
        c = canvas.Canvas(pdf, pagesize=(card_w, card_h))
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, card_w, card_h, stroke=0, fill=1)
        _draw_business_card(c, listing, request, lang, 0, 0, card_w, card_h)
    else:
        page_size = landscape(A4)
        c = canvas.Canvas(pdf, pagesize=page_size)
        W, H = page_size
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, W, H, stroke=0, fill=1)

        cols = 3
        rows = 3
        gap_x = 6 * mm
        gap_y = 6 * mm
        margin_x = (W - (cols * card_w + (cols - 1) * gap_x)) / 2
        margin_y = (H - (rows * card_h + (rows - 1) * gap_y)) / 2

        for row in range(rows):
            for col in range(cols):
                x = margin_x + col * (card_w + gap_x)
                y = H - margin_y - (row + 1) * card_h - row * gap_y
                _draw_business_card(c, listing, request, lang, x, y, card_w, card_h)

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _make_gift_card_pdf_legacy_unused(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    colors = _brand_colors(str(listing.get("plan") or "standard"))
    url = _public_listing_url(request, listing.get("slug") or "")
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")
    hero = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    sig = _signature_image_path(listing)

    c.setFillColorRGB(0.97, 0.97, 0.98)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    outer_x = 18 * mm
    outer_y = 48 * mm
    outer_w = W - 36 * mm
    outer_h = 110 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*colors["line"])
    c.setLineWidth(1)
    c.roundRect(outer_x, outer_y, outer_w, outer_h, 7 * mm, stroke=1, fill=1)

    left_w = outer_w * 0.42
    if not _draw_cover_photo(c, hero or sig, outer_x, outer_y, left_w, outer_h):
        c.setFillColorRGB(*colors["accent2"])
        c.roundRect(outer_x, outer_y, left_w, outer_h, 7 * mm, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFillAlpha(0.18)
    c.roundRect(outer_x, outer_y, left_w, outer_h, 7 * mm, stroke=0, fill=1)
    c.setFillAlpha(1)

    right_x = outer_x + left_w + 6 * mm
    right_w = outer_w - left_w - 12 * mm
    _draw_badge(c, right_x, outer_y + outer_h - 14 * mm, "GIFT CARD" if lang == "en" else "GAVEKORT", colors["accent"], font_size=8)
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica-Bold", 24)
    c.drawString(right_x, outer_y + outer_h - 26 * mm, str(listing.get("name") or "Kitchen")[:24])
    c.setFillColorRGB(*colors["muted"])
    c.setFont("Helvetica", 11)
    c.drawString(right_x, outer_y + outer_h - 33 * mm, "A thoughtful local food gift" if lang == "en" else "En profesjonell lokal matgave")

    labels = ["To" if lang == "en" else "Til", "From" if lang == "en" else "Fra", "Value" if lang == "en" else "Beløp"]
    line_y = outer_y + outer_h - 48 * mm
    for i, lab in enumerate(labels):
        yy = line_y - i * 16 * mm
        c.setFillColorRGB(*colors["muted"])
        c.setFont("Helvetica-Bold", 9)
        c.drawString(right_x, yy + 3 * mm, lab)
        c.setStrokeColorRGB(*colors["line"])
        c.setLineWidth(0.9)
        c.line(right_x, yy, right_x + right_w - 50 * mm, yy)

    message = "Scan menu to redeem online." if lang == "en" else "Skann menyen for å løse inn digitalt."
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica", 10.8)
    msg_y = outer_y + 16 * mm
    for line in _wrap_lines(message, right_w - 52 * mm, "Helvetica", 9.2)[:2]:
        c.drawString(right_x, msg_y, line)
        msg_y += 4.6 * mm

    qr_size = 28 * mm
    qx = outer_x + outer_w - qr_size - 9 * mm
    qy = outer_y + 12 * mm
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(qx - 2 * mm, qy - 2 * mm, qr_size + 4 * mm, qr_size + 4 * mm, 3 * mm, stroke=0, fill=1)
    c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask="auto")
    c.setFillColorRGB(*colors["muted"])
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(qx + qr_size / 2, qy - 4.5 * mm, "Scan to order" if lang == "en" else "Skann for å bestille")

    c.setStrokeColorRGB(*colors["line"])
    c.line(outer_x, outer_y - 6 * mm, outer_x + outer_w, outer_y - 6 * mm)
    c.setFillColorRGB(*colors["muted"])
    c.setFont("Helvetica", 8.2)
    c.drawString(outer_x, outer_y - 11 * mm, _safe_contact_line(listing)[:70])
    c.drawRightString(outer_x + outer_w, outer_y - 11 * mm, url[:78])

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _make_promo_cards_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    colors = _brand_colors(str(listing.get("plan") or "standard"))
    url = _public_listing_url(request, listing.get("slug") or "")
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=5, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")
    title = str(listing.get("name") or "Kitchen")
    prompts = [
        ("Order again" if lang == "en" else "Bestill igjen", "Fast local pickup" if lang == "en" else "Rask lokal henting"),
        ("Share with a friend" if lang == "en" else "Del med en venn", "A kitchen worth trying" if lang == "en" else "Et kjøkken verdt å prøve"),
        ("Office lunch" if lang == "en" else "Kontorlunsj", "Simple food for teams" if lang == "en" else "Enkel mat for team"),
        ("Pickup made easy" if lang == "en" else "Enkel henting", "Scan and view the menu" if lang == "en" else "Skann og se menyen"),
        ("Food by request" if lang == "en" else "Mat på bestilling", "Fresh local dishes" if lang == "en" else "Ferske lokale retter"),
        ("Gift a meal" if lang == "en" else "Gi bort et måltid", "Perfect for someone nearby" if lang == "en" else "Perfekt for noen i nærheten"),
        ("New customer" if lang == "en" else "Ny kunde", "Start with the menu" if lang == "en" else "Start med menyen"),
        ("Neighborhood favorite" if lang == "en" else "Nabolagsfavoritt", "Made with care" if lang == "en" else "Laget med omtanke"),
    ]
    photo_paths = _listing_photo_paths(listing) or []

    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    margin = 12 * mm
    gap = 6 * mm
    card_w = (W - 2 * margin - gap) / 2
    card_h = (H - 2 * margin - 3 * gap) / 4
    idx = 0
    for row in range(4):
        for col in range(2):
            x = margin + col * (card_w + gap)
            y = H - margin - (row + 1) * card_h - row * gap
            headline, sub = prompts[idx]
            photo = photo_paths[idx % len(photo_paths)] if photo_paths else None
            idx += 1
            c.setFillColorRGB(1, 1, 1)
            c.setStrokeColorRGB(*colors["line"])
            c.roundRect(x, y, card_w, card_h, 4 * mm, stroke=1, fill=1)
            photo_w = 24 * mm
            if _draw_cover_photo(c, photo, x, y, photo_w, card_h):
                c.setFillColorRGB(0, 0, 0)
                c.setFillAlpha(0.08)
                c.rect(x, y, photo_w, card_h, stroke=0, fill=1)
                c.setFillAlpha(1)
            else:
                c.setFillColorRGB(*colors["accent2"])
                c.roundRect(x, y, photo_w, card_h, 4 * mm, stroke=0, fill=1)
            c.setFillColorRGB(*colors["accent"])
            c.rect(x + photo_w, y + card_h - 2 * mm, card_w - photo_w, 2 * mm, stroke=0, fill=1)
            tx = x + photo_w + 4 * mm
            _draw_badge(c, tx, y + card_h - 11 * mm, title[:18], colors["accent"], font_size=7, h=6.5 * mm, pad_x=3 * mm)
            c.setFillColorRGB(*colors["ink"])
            c.setFont("Helvetica-Bold", 12)
            c.drawString(tx, y + card_h - 18 * mm, headline[:22])
            c.setFillColorRGB(*colors["muted"])
            c.setFont("Helvetica", 8.5)
            for n, line in enumerate(_wrap_lines(sub, card_w - photo_w - 34 * mm, "Helvetica", 8.5)[:2]):
                c.drawString(tx, y + card_h - 24 * mm - n * 4.3 * mm, line)
            qr_size = 16 * mm
            qx = x + card_w - qr_size - 4 * mm
            qy = y + 4.5 * mm
            c.setFillColorRGB(1, 1, 1)
            c.roundRect(qx - 1.4 * mm, qy - 1.4 * mm, qr_size + 2.8 * mm, qr_size + 2.8 * mm, 2 * mm, stroke=0, fill=1)
            c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask="auto")
            c.setFillColorRGB(*colors["muted"])
            c.setFont("Helvetica-Bold", 7)
            c.drawString(tx, y + 9 * mm, "Scan menu" if lang == "en" else "Skann meny")
            c.setFont("Helvetica", 6.8)
            c.drawString(tx, y + 5 * mm, url[:24])
    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _pdf_stream_response(pdf: BytesIO, filename: str, download: int = 1):
    disposition = 'attachment' if int(download or 0) == 1 else 'inline'
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'}
    )


@app.get("/api/owner/{token}/flyer.pdf")
def owner_flyer_pdf(token: str, request: Request, lang: str = "en", download: int = 1):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'
    pdf = _make_flyer_pdf(listing, request, lang=lang)
    fn = f"{listing.get('slug')}-flyer-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.get("/api/owner/{token}/flyer2.pdf")
def owner_flyer2_pdf(
    token: str,
    request: Request,
    lang: str = "en",
    download: int = 1,
    headline: str | None = None,
    support: str | None = None,
    accent: str | None = None,
    focal_x: float | None = None,
    focal_y: float | None = None,
    zoom: float | None = None,
):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'

    working_listing = dict(listing or {})
    lang_key = 'no' if lang == 'no' else 'en'

    if headline is not None:
        existing = working_listing.get("flyer_headline") if isinstance(working_listing.get("flyer_headline"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = headline
        working_listing["flyer_headline"] = existing
    if support is not None:
        existing = working_listing.get("flyer_support") if isinstance(working_listing.get("flyer_support"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = support
        working_listing["flyer_support"] = existing
    if accent is not None and re.fullmatch(r"#[0-9a-fA-F]{6}", accent or ""):
        working_listing["flyer_accent"] = accent
    if focal_x is not None:
        working_listing["flyer_image_focal_x"] = max(0, min(100, float(focal_x)))
    if focal_y is not None:
        working_listing["flyer_image_focal_y"] = max(0, min(100, float(focal_y)))
    if zoom is not None:
        working_listing["flyer_image_zoom"] = max(100, min(200, float(zoom)))

    try:
        pdf = _make_flyer2_pdf(working_listing, request, lang=lang)
    except Exception:
        safe_listing = dict(working_listing or {})
        safe_listing["contact"] = safe_listing.get("contact") if isinstance(safe_listing.get("contact"), dict) else {}
        safe_listing["flyer_image_focal_x"] = max(0, min(100, float(safe_listing.get("flyer_image_focal_x") or 50)))
        safe_listing["flyer_image_focal_y"] = max(0, min(100, float(safe_listing.get("flyer_image_focal_y") or 50)))
        safe_listing["flyer_image_zoom"] = max(100, min(200, float(safe_listing.get("flyer_image_zoom") or 100)))
        pdf = _make_flyer2_pdf(safe_listing, request, lang=lang)
    fn = f"{listing.get('slug')}-poster2-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.get("/api/owner/{token}/flyer3.pdf")
def owner_flyer3_pdf(
    token: str,
    request: Request,
    lang: str = "en",
    download: int = 1,
    headline: str | None = None,
    support: str | None = None,
    accent: str | None = None,
    focal_x: float | None = None,
    focal_y: float | None = None,
    zoom: float | None = None,
):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'

    working_listing = dict(listing or {})
    lang_key = 'no' if lang == 'no' else 'en'

    if headline is not None:
        existing = working_listing.get("poster3_headline") if isinstance(working_listing.get("poster3_headline"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = headline
        working_listing["poster3_headline"] = existing
    if support is not None:
        existing = working_listing.get("poster3_support") if isinstance(working_listing.get("poster3_support"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = support
        working_listing["poster3_support"] = existing
    if accent is not None and re.fullmatch(r"#[0-9a-fA-F]{6}", accent or ""):
        working_listing["poster3_accent"] = accent
    if focal_x is not None:
        working_listing["poster3_image_focal_x"] = max(0, min(100, float(focal_x)))
    if focal_y is not None:
        working_listing["poster3_image_focal_y"] = max(0, min(100, float(focal_y)))
    if zoom is not None:
        working_listing["poster3_image_zoom"] = max(100, min(200, float(zoom)))

    try:
        pdf = _make_flyer3_pdf(working_listing, request, lang=lang)
    except Exception:
        safe_listing = dict(working_listing or {})
        safe_listing["contact"] = safe_listing.get("contact") if isinstance(safe_listing.get("contact"), dict) else {}
        safe_listing["poster3_image_focal_x"] = max(0, min(100, float(safe_listing.get("poster3_image_focal_x") or safe_listing.get("flyer_image_focal_x") or 50)))
        safe_listing["poster3_image_focal_y"] = max(0, min(100, float(safe_listing.get("poster3_image_focal_y") or safe_listing.get("flyer_image_focal_y") or 50)))
        safe_listing["poster3_image_zoom"] = max(100, min(200, float(safe_listing.get("poster3_image_zoom") or safe_listing.get("flyer_image_zoom") or 100)))
        pdf = _make_flyer3_pdf(safe_listing, request, lang=lang)
    fn = f"{listing.get('slug')}-poster3-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)




def _make_flyer3_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    title = str(listing.get("name") or ("Kitchen" if lang == "en" else "Kjøkken")).strip()
    url = _public_listing_url(request, listing.get("slug") or "")
    accent = _hex_to_rgb01(listing.get("poster3_accent") or listing.get("flyer_accent") or "#f39a21")
    dark = (0.15, 0.14, 0.18)
    warm_white = (0.985, 0.98, 0.965)
    soft_text = (0.83, 0.86, 0.92)
    
    hero_path = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    img_paths = _resolve_marketing_image_paths(listing, limit=3)
    if not img_paths and hero_path and hero_path.exists():
        img_paths = [hero_path]
    if not img_paths:
        img_paths = [None, None, None]
    while len(img_paths) < 3:
        img_paths.append(img_paths[-1])

    headline = _poster3_headline(listing, lang)
    support = _poster3_support(listing, lang)
    contact_line = _safe_contact_line(listing) or url.replace('https://','').replace('http://','')
    ink_color = "#161616"
    bg_color = "#f7f1e8"

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")

    margin = 11 * mm
    art_x = margin
    art_y = margin
    art_w = W - 2 * margin
    art_h = H - 2 * margin

    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Outer card
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(art_x, art_y, art_w, art_h, 8 * mm, stroke=0, fill=1)

    left_w = art_w * 0.58
    panel_x = art_x + art_w * 0.54
    panel_w = art_x + art_w - panel_x

    # Hero image as the design foundation on the left side, clipped to the poster card.
    c.saveState()
    outer_clip = c.beginPath()
    outer_clip.roundRect(art_x, art_y, art_w, art_h, 8 * mm)
    c.clipPath(outer_clip, stroke=0, fill=0)
    if not _draw_cover_photo(c, hero_path or img_paths[0], art_x, art_y, left_w + 12 * mm, art_h):
        c.setFillColorRGB(0.92, 0.91, 0.88)
        c.rect(art_x, art_y, left_w + 12 * mm, art_h, stroke=0, fill=1)
    c.restoreState()

    # Orange flowing fields on top of the hero image.
    orange_field = c.beginPath()
    orange_field.moveTo(art_x, art_y)
    orange_field.lineTo(art_x + left_w - 22 * mm, art_y)
    orange_field.curveTo(art_x + left_w - 38 * mm, art_y + art_h * 0.22, art_x + left_w - 34 * mm, art_y + art_h * 0.82, art_x + left_w - 10 * mm, art_y + art_h)
    orange_field.lineTo(art_x, art_y + art_h)
    orange_field.close()
    c.setFillColorRGB(*accent)
    c.drawPath(orange_field, stroke=0, fill=1)

    # Main image window cut through the orange field.
    hero_window = c.beginPath()
    hero_window.moveTo(art_x + 28 * mm, art_y + art_h)
    hero_window.lineTo(art_x + left_w + 8 * mm, art_y + art_h)
    hero_window.curveTo(art_x + left_w - 24 * mm, art_y + art_h * 0.82, art_x + left_w - 20 * mm, art_y + art_h * 0.24, art_x + left_w + 5 * mm, art_y)
    hero_window.lineTo(art_x + 20 * mm, art_y)
    hero_window.curveTo(art_x + 56 * mm, art_y + art_h * 0.26, art_x + 50 * mm, art_y + art_h * 0.76, art_x + 28 * mm, art_y + art_h)
    hero_window.close()
    c.setFillColorRGB(1, 1, 1)
    c.drawPath(hero_window, stroke=0, fill=1)

    c.saveState()
    hero_img_clip = c.beginPath()
    hero_img_clip.moveTo(art_x + 28 * mm, art_y + art_h)
    hero_img_clip.lineTo(art_x + left_w + 6 * mm, art_y + art_h)
    hero_img_clip.curveTo(art_x + left_w - 26 * mm, art_y + art_h * 0.82, art_x + left_w - 22 * mm, art_y + art_h * 0.24, art_x + left_w + 3 * mm, art_y)
    hero_img_clip.lineTo(art_x + 22 * mm, art_y)
    hero_img_clip.curveTo(art_x + 56 * mm, art_y + art_h * 0.26, art_x + 52 * mm, art_y + art_h * 0.76, art_x + 28 * mm, art_y + art_h)
    hero_img_clip.close()
    c.clipPath(hero_img_clip, stroke=0, fill=0)
    if not _draw_cover_photo(c, hero_path or img_paths[0], art_x + 14 * mm, art_y, left_w + 8 * mm, art_h):
        c.setFillColorRGB(0.93, 0.92, 0.90)
        c.rect(art_x + 14 * mm, art_y, left_w + 8 * mm, art_h, stroke=0, fill=1)
    c.restoreState()

    # Thin white ribbon between left and right for a cleaner transition.
    ribbon = c.beginPath()
    ribbon.moveTo(panel_x - 5.5 * mm, art_y)
    ribbon.curveTo(panel_x - 12 * mm, art_y + art_h * 0.24, panel_x - 12 * mm, art_y + art_h * 0.76, panel_x - 4.5 * mm, art_y + art_h)
    ribbon.lineTo(panel_x - 0.6 * mm, art_y + art_h)
    ribbon.curveTo(panel_x - 6.5 * mm, art_y + art_h * 0.76, panel_x - 6.5 * mm, art_y + art_h * 0.24, panel_x + 0.8 * mm, art_y)
    ribbon.close()
    c.setFillColorRGB(1, 1, 1)
    c.drawPath(ribbon, stroke=0, fill=1)

    # Dark info panel with a single smooth curved edge.
    panel = c.beginPath()
    panel.moveTo(panel_x + 5 * mm, art_y)
    panel.lineTo(art_x + art_w, art_y)
    panel.lineTo(art_x + art_w, art_y + art_h)
    panel.lineTo(panel_x + 7 * mm, art_y + art_h)
    panel.curveTo(panel_x - 6 * mm, art_y + art_h * 0.78, panel_x - 6 * mm, art_y + art_h * 0.22, panel_x + 5 * mm, art_y)
    panel.close()
    c.setFillColorRGB(*dark)
    c.drawPath(panel, stroke=0, fill=1)

    # Two menu circles with a tighter horizontal relationship and more vertical spread.
    circles = [
        (art_x + 43 * mm, art_y + 167 * mm, 35 * mm),
        (art_x + 56 * mm, art_y + 88 * mm, 37 * mm),
    ]
    for idx, (cx, cy, d) in enumerate(circles):
        _draw_circle_photo(c, img_paths[idx], cx, cy, d, border_rgb=(1, 1, 1), border_mm=2.1)

    # Left headline block: larger, elegant, consistent white script styling.
    left_text_x = art_x + 14 * mm
    fresh_text = "Fresh" if lang == "en" else "Fersk"
    food_text = "Food"
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Times-Italic", 39)
    c.drawString(left_text_x + 6 * mm, art_y + 44 * mm, fresh_text)
    c.drawString(left_text_x + 29 * mm, art_y + 22.5 * mm, food_text)

    # Right content.
    inner_x = panel_x + 19 * mm
    inner_right = art_x + art_w - 16 * mm
    inner_top = art_y + art_h - 18 * mm

    c.setFillColorRGB(*accent)
    c.setFont("Helvetica-Bold", 10.8)
    c.drawString(inner_x, inner_top, _truncate_with_ellipsis(title.upper(), inner_right - inner_x, "Helvetica-Bold", 10.8))

    c.setFillColorRGB(1, 1, 1)
    head_fs = 17
    head_lines = _wrap_lines(headline, inner_right - inner_x, "Helvetica-Bold", head_fs)[:4]
    y = inner_top - 12 * mm
    c.setFont("Helvetica-Bold", head_fs)
    for line in head_lines:
        c.drawString(inner_x, y, line)
        y -= 7.1 * mm

    c.setFillColorRGB(*soft_text)
    support_fs = 10
    support_lh = 4.8 * mm
    c.setFont("Helvetica", support_fs)
    # Let the support copy breathe further down toward the menu area, instead of
    # cutting it off after only a few short lines.
    provisional_menu_y = art_y + 88 * mm
    available_support_h = max(12 * mm, (y - 1.3 * mm) - (provisional_menu_y + 10 * mm))
    max_support_lines = max(4, int(available_support_h / support_lh))
    support_lines = _wrap_lines(support, inner_right - inner_x - 1 * mm, "Helvetica", support_fs)[:max_support_lines]
    y -= 1.3 * mm
    for line in support_lines:
        c.drawString(inner_x, y, line)
        y -= support_lh

    menu_titles = []
    for item in (listing.get('menu') or []):
        if not isinstance(item, dict):
            continue
        raw = item.get('title') if item.get('title') is not None else item.get('name')
        if isinstance(raw, dict):
            txt = str(raw.get(lang) or raw.get('en') or raw.get('no') or '').strip()
        else:
            txt = str(raw or '').strip()
        if txt and txt not in menu_titles:
            menu_titles.append(txt)
        if len(menu_titles) >= 5:
            break
    if not menu_titles:
        menu_titles = ["Fresh homemade favorites"] if lang == 'en' else ["Hjemmelagde favoritter"]

    # Move the menu somewhat back up so the right side feels more balanced,
    # while still leaving a generous support-text area above it.
    section_y = max(art_y + 102 * mm, min(y - 7 * mm, art_y + 116 * mm))
    c.setFillColorRGB(*accent)
    c.roundRect(inner_x, section_y + 1.4 * mm, 17 * mm, 1.5 * mm, 0.8 * mm, stroke=0, fill=1)
    c.roundRect(inner_x + 35 * mm, section_y + 1.4 * mm, max(20 * mm, inner_right - (inner_x + 35 * mm)), 1.5 * mm, 0.8 * mm, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(inner_x + 19 * mm, section_y - 0.2 * mm, "MENU" if lang == 'en' else "MENY")

    c.setFont("Helvetica", 10.4)
    yy = section_y - 8.5 * mm
    for t in menu_titles:
        t = _truncate_with_ellipsis(t, (inner_right - inner_x) - 1 * mm, "Helvetica", 10.4)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(inner_x, yy, t)
        dots_start = inner_x + min(stringWidth(t, "Helvetica", 10.4) + 4 * mm, (inner_right - inner_x) - 14 * mm)
        dots_end = inner_right
        if dots_end - dots_start > 10 * mm:
            c.setStrokeColorRGB(0.88, 0.75, 0.46)
            c.setLineWidth(0.6)
            c.setDash(0.8 * mm, 1.0 * mm)
            c.line(dots_start, yy + 1.4 * mm, dots_end, yy + 1.4 * mm)
            c.setDash()
        yy -= 7.0 * mm

    footer_x = panel_x + 13 * mm
    footer_y = art_y + 11 * mm
    footer_w = panel_w - 26 * mm
    footer_h = 36 * mm
    c.setFillColorRGB(0.11, 0.12, 0.16)
    c.roundRect(footer_x, footer_y, footer_w, footer_h, 6 * mm, stroke=0, fill=1)

    qr_size = 22 * mm
    qx = footer_x + 6.5 * mm
    qy = footer_y + (footer_h - qr_size) / 2
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(qx - 2.2 * mm, qy - 2.2 * mm, qr_size + 4.4 * mm, qr_size + 4.4 * mm, 4 * mm, stroke=0, fill=1)
    c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask='auto')

    text_x = qx + qr_size + 6.5 * mm
    text_w = max(22 * mm, footer_x + footer_w - text_x - 4 * mm)
    c.setFillColorRGB(1, 1, 1)
    qr_title = "Scan to view full menu" if lang == 'en' else 'Skann for å se hele menyen'
    qr_title_lines = _wrap_lines(qr_title, text_w, "Helvetica-Bold", 9.2)[:2]
    c.setFont("Helvetica-Bold", 9.2)
    title_y = footer_y + 23.8 * mm
    for line in qr_title_lines:
        c.drawString(text_x, title_y, line)
        title_y -= 4.1 * mm
    c.setFillColorRGB(*soft_text)
    c.setFont("Helvetica", 8.8)
    footer_lines = _wrap_lines(contact_line, text_w, "Helvetica", 8.8)[:2]
    fy = footer_y + 12.2 * mm
    for line in footer_lines:
        c.drawString(text_x, fy, line)
        fy -= 4.0 * mm

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf

def _make_flyer_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    colors = _brand_colors(str(listing.get("plan") or "standard"))
    page_margin = 12 * mm
    url = _public_listing_url(request, listing.get("slug") or "")
    title = str(listing.get("name") or "Kitchen").strip()
    subtitle = f"{listing.get('area','')} · {listing.get('city','')}".strip(" ·")
    tagline = _flyer_support_text(listing, lang)
    sig_title, sig_desc, _sig_price_unused = _get_signature_dish(listing, lang)
    contact_line = _safe_contact_line(listing)
    hero_img = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    flyer_accent = _hex_to_rgb01(listing.get("flyer_accent") or "#8557c7")
    flyer_accent_soft = tuple(min(1.0, (v * 0.22) + 0.78) for v in flyer_accent)
    flyer_img_focal_x = float(listing.get("flyer_image_focal_x") or 50)
    flyer_img_focal_y = float(listing.get("flyer_image_focal_y") or 50)
    flyer_img_zoom = float(listing.get("flyer_image_zoom") or 100)
    sig_img = _signature_image_path(listing)

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")

    c.setFillColorRGB(0.97, 0.96, 0.94)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Artboard
    art_x = page_margin
    art_y = page_margin
    art_w = W - (2 * page_margin)
    art_h = H - (2 * page_margin)

    # Left hero image area
    image_w = art_w * 0.62
    image_h = art_h
    image_x = art_x
    image_y = art_y
    drew_hero = _draw_cover_photo_adjusted(c, hero_img, image_x, image_y, image_w, image_h, focal_x=flyer_img_focal_x, focal_y=flyer_img_focal_y, zoom=flyer_img_zoom)
    if not drew_hero:
        c.setFillColorRGB(*flyer_accent_soft)
        c.rect(image_x, image_y, image_w, image_h, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFillAlpha(0.14)
    c.rect(image_x, image_y, image_w, image_h, stroke=0, fill=1)
    c.setFillAlpha(1)

    # Diagonal accent overlay to make the flyer feel more commercial/editorial
    panel_overlap = 14 * mm
    panel_x = image_x + image_w - panel_overlap
    panel_w = art_x + art_w - panel_x
    panel_y = art_y
    panel_h = art_h

    c.setFillColorRGB(0.985, 0.975, 0.96)
    c.roundRect(panel_x, panel_y, panel_w, panel_h, 0, stroke=0, fill=1)

    wedge = c.beginPath()
    wedge.moveTo(panel_x, panel_y)
    wedge.lineTo(panel_x, panel_y + panel_h)
    wedge.lineTo(panel_x - 26 * mm, panel_y + panel_h)
    wedge.lineTo(panel_x - 5 * mm, panel_y)
    wedge.close()
    flyer_violet = flyer_accent
    flyer_violet_light = flyer_accent_soft
    c.setFillColorRGB(*flyer_violet)
    c.setFillAlpha(0.70)
    c.drawPath(wedge, stroke=0, fill=1)
    c.setFillAlpha(1)

    # Image text block
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(image_x + 9 * mm, image_y + image_h - 16 * mm, (title[:28]).upper())
    if subtitle:
        c.setFont("Helvetica", 10.8)
        c.drawString(image_x + 9 * mm, image_y + image_h - 22 * mm, subtitle[:34])

    # Signature dish tile inside image area
    tile_w = 52 * mm
    tile_h = 48 * mm
    tile_x = image_x + 9 * mm
    tile_y = image_y + 11 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setFillAlpha(0.98)
    c.roundRect(tile_x, tile_y, tile_w, tile_h, 3 * mm, stroke=0, fill=1)
    c.setFillAlpha(1)
    inner_img_h = 25 * mm
    if _draw_cover_photo(c, sig_img, tile_x + 3 * mm, tile_y + tile_h - inner_img_h - 3 * mm, tile_w - 6 * mm, inner_img_h):
        pass
    else:
        c.setFillColorRGB(*flyer_violet_light)
        c.roundRect(tile_x + 3 * mm, tile_y + tile_h - inner_img_h - 3 * mm, tile_w - 6 * mm, inner_img_h, 2 * mm, stroke=0, fill=1)
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica-Bold", 7.3)
    c.drawString(tile_x + 4 * mm, tile_y + 16 * mm, "SIGNATURE DISH" if lang == "en" else "SIGNATURRETT")
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(tile_x + 4 * mm, tile_y + 11 * mm, (sig_title or ("Fresh homemade menu" if lang == "en" else "Fersk hjemmelaget meny"))[:23])
    c.setFillColorRGB(*colors["muted"])
    c.setFont("Helvetica", 7.4)
    desc_line = (sig_desc or ("Made with care and ready to order." if lang == "en" else "Laget med omtanke og klar til bestilling.")).strip()
    for i, line in enumerate(_wrap_lines(desc_line, tile_w - 8 * mm, "Helvetica", 7.4)[:2]):
        c.drawString(tile_x + 4 * mm, tile_y + 6.2 * mm - i * 3.6 * mm, line)

    # Right editorial panel content
    inner_x = panel_x + 12 * mm
    inner_right = art_x + art_w - 10 * mm
    inner_w = inner_right - inner_x
    top_y = art_y + art_h - 15 * mm

    # Small label
    _draw_badge(c, inner_x, top_y - 1 * mm, "LOCAL ASIAN KITCHEN" if lang == "en" else "LOKALT ASIATISK KJØKKEN", flyer_violet, font_size=9.1, h=8.4 * mm, pad_x=4.1 * mm)

    # Kitchen name + headline
    c.setFillColorRGB(*flyer_violet)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inner_x, top_y - 12 * mm, title[:26])
    headline_lines = _flyer_headline_lines(listing, lang)
    # Keep the headline in the editorial panel, but make it feel more like a
    # clean ad headline: uppercase, slightly larger, with more breathing room
    # between the lines.
    headline_x = inner_x
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica-Bold", 20.5)
    hy = top_y - 26 * mm
    line_gap = 10.0 * mm
    for i, line in enumerate(headline_lines):
        c.drawString(headline_x, hy - i * line_gap, line)

    # Support copy
    support = tagline or ("Discover the menu, see the dishes and order in seconds." if lang == "en" else "Oppdag menyen, se rettene og bestill på få sekunder.")
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica", 16.2)
    sy = top_y - 58 * mm
    for line in _wrap_lines(support, inner_w - 4 * mm, "Helvetica", 16.2)[:3]:
        c.drawString(inner_x, sy, line)
        sy -= 6.3 * mm

    # QR call-to-action and code in a clean right-column zone (no box)
    qr_zone_x = inner_x
    qr_zone_y = art_y + 24 * mm
    qr_zone_w = inner_w
    qr_size = 41 * mm
    c.setFillColorRGB(*flyer_violet)
    c.setFont("Helvetica-Bold", 13.2)
    qr_head = ["SCAN TO VIEW MENU"] if lang == "en" else ["SKANN FOR Å SE MENY"]
    c.drawCentredString(qr_zone_x + (qr_zone_w / 2), qr_zone_y + qr_size + 8.2 * mm, qr_head[0])

    qx = qr_zone_x + (qr_zone_w - qr_size) / 2
    qy = qr_zone_y
    c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask="auto")

    # Contact line in same badge style as the category label, centered under QR
    contact_y = art_y + 8.6 * mm
    contact_label = "CONTACT" if lang == "en" else "KONTAKT"
    badge_fill = flyer_violet
    contact_text = f"{contact_label}  {contact_line[:30]}" if contact_line else url.replace("https://", "").replace("http://", "")[:30]
    contact_font = "Helvetica"
    contact_fs = 10.8
    contact_pad_x = 4.2 * mm
    contact_h = 8.6 * mm
    contact_tw = c.stringWidth(contact_text, contact_font, contact_fs)
    contact_box_w = contact_tw + 2 * contact_pad_x
    contact_box_x = inner_x + (inner_w - contact_box_w) / 2
    contact_box_y = contact_y - 3.6 * mm
    c.setFillColorRGB(*badge_fill)
    c.roundRect(contact_box_x, contact_box_y, contact_box_w, contact_h, 3.6 * mm, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(contact_font, contact_fs)
    c.drawCentredString(contact_box_x + (contact_box_w / 2), contact_box_y + 2.55 * mm, contact_text)

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _make_flyer2_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    title = str(listing.get("name") or ("Kitchen" if lang == "en" else "Kjøkken"))
    url = _public_listing_url(request, listing.get("slug") or "")
    contact_line = _safe_contact_line(listing)
    hero_img = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    sig_img = _signature_image_path(listing)
    sig_title, sig_desc, _ = _get_signature_dish(listing, lang)
    headline = " ".join(_flyer_headline_lines(listing, lang)).strip()
    support = _flyer_support_text(listing, lang) or ("Discover the menu, scan the QR and order in seconds." if lang == "en" else "Se menyen, skann QR-koden og bestill på få sekunder.")
    accent = _hex_to_rgb01(listing.get("flyer_accent") or "#8557c7")
    accent_soft = tuple(min(1.0, (v * 0.18) + 0.82) for v in accent)
    flyer_img_focal_x = float(listing.get("flyer_image_focal_x") or 50)
    flyer_img_focal_y = float(listing.get("flyer_image_focal_y") or 50)
    flyer_img_zoom = float(listing.get("flyer_image_zoom") or 100)
    ink_color = "#161616"
    bg_color = "#f7f1e8"

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")

    c.setFillColorRGB(0.97, 0.96, 0.94)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    page_margin = 11 * mm
    art_x = page_margin
    art_y = page_margin
    art_w = W - (2 * page_margin)
    art_h = H - (2 * page_margin)

    c.setFillColorRGB(1, 1, 1)
    c.roundRect(art_x, art_y, art_w, art_h, 7 * mm, stroke=0, fill=1)

    top_h = art_h * 0.44
    drew_hero = _draw_cover_photo_adjusted(c, hero_img, art_x, art_y + art_h - top_h, art_w, top_h, focal_x=flyer_img_focal_x, focal_y=flyer_img_focal_y, zoom=flyer_img_zoom)
    if not drew_hero:
        c.setFillColorRGB(*accent_soft)
        c.roundRect(art_x, art_y + art_h - top_h, art_w, top_h, 7 * mm, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFillAlpha(0.18)
    c.roundRect(art_x, art_y + art_h - top_h, art_w, top_h, 7 * mm, stroke=0, fill=1)
    c.setFillAlpha(1)

    dark = (0.08, 0.10, 0.14)
    bottom_h = art_h * 0.60
    bottom_y = art_y
    c.setFillColorRGB(*dark)
    c.roundRect(art_x, bottom_y, art_w, bottom_h, 10 * mm, stroke=0, fill=1)

    circle_d = 41 * mm
    circle_x = art_x + art_w - circle_d - 12 * mm
    circle_y = art_y + art_h - top_h - (circle_d * 0.52)
    c.setFillColorRGB(1, 1, 1)
    c.circle(circle_x + circle_d/2, circle_y + circle_d/2, circle_d/2 + 2.2 * mm, stroke=0, fill=1)
    c.saveState()
    p = c.beginPath()
    p.circle(circle_x + circle_d/2, circle_y + circle_d/2, circle_d/2)
    c.clipPath(p, stroke=0, fill=0)
    if not _draw_cover_photo(c, sig_img, circle_x, circle_y, circle_d, circle_d):
        c.setFillColorRGB(*accent_soft)
        c.circle(circle_x + circle_d/2, circle_y + circle_d/2, circle_d/2, stroke=0, fill=1)
    c.restoreState()

    text_x = art_x + 11 * mm
    text_top = art_y + bottom_h - 18 * mm
    c.setFillColorRGB(*accent)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(text_x, text_top, title[:34].upper())
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 27)
    headline_lines = _wrap_lines(headline, art_w - 30 * mm, "Helvetica-Bold", 27)[:3]
    hy = text_top - 12 * mm
    for i, line in enumerate(headline_lines):
        c.drawString(text_x, hy - i * 10.5 * mm, line)
    c.setFillColorRGB(*accent)
    c.roundRect(text_x, hy - len(headline_lines)*10.5*mm - 2*mm, 20 * mm, 1.9 * mm, 1 * mm, stroke=0, fill=1)

    support_y = hy - len(headline_lines) * 10.5 * mm - 10 * mm
    c.setFillColorRGB(0.86, 0.88, 0.92)
    c.setFont("Helvetica", 11.8)
    for i, line in enumerate(_wrap_lines(support, art_w * 0.54, "Helvetica", 11.8)[:4]):
        c.drawString(text_x, support_y - i * 5.0 * mm, line)

    sig_block_x = circle_x - 4 * mm
    sig_block_y = art_y + 55 * mm
    c.setFillColorRGB(*accent)
    c.setFont("Helvetica-Bold", 9.4)
    c.drawString(sig_block_x, sig_block_y + 12 * mm, "SIGNATURE DISH" if lang == "en" else "SIGNATURRETT")
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 15)
    for i, line in enumerate(_wrap_lines(sig_title or ("Signature dish" if lang == "en" else "Signaturrett"), 54 * mm, "Helvetica-Bold", 15)[:2]):
        c.drawString(sig_block_x, sig_block_y + 6 * mm - i * 6 * mm, line)
    c.setFillColorRGB(0.80, 0.83, 0.88)
    c.setFont("Helvetica", 9.4)
    for i, line in enumerate(_wrap_lines(sig_desc or ("Made with care and ready to order." if lang == "en" else "Laget med omtanke og klar til bestilling."), 54 * mm, "Helvetica", 9.4)[:3]):
        c.drawString(sig_block_x, sig_block_y - 3 * mm - i * 4.1 * mm, line)

    footer_x = art_x + 10 * mm
    footer_y = art_y + 10 * mm
    footer_w = art_w - 20 * mm
    footer_h = 28 * mm
    c.setFillColorRGB(0.12, 0.15, 0.21)
    c.roundRect(footer_x, footer_y, footer_w, footer_h, 5 * mm, stroke=0, fill=1)
    q_size = 19 * mm
    qx = footer_x + footer_w - q_size - 5 * mm
    qy = footer_y + (footer_h - q_size) / 2
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(qx - 2 * mm, qy - 2 * mm, q_size + 4 * mm, q_size + 4 * mm, 3 * mm, stroke=0, fill=1)
    c.drawImage(ImageReader(qr_img), qx, qy, width=q_size, height=q_size, mask="auto")
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10.8)
    c.drawString(footer_x + 5 * mm, footer_y + 17 * mm, "SCAN TO VIEW MENU" if lang == "en" else "SKANN FOR Å SE MENY")
    c.setFillColorRGB(0.83, 0.86, 0.90)
    c.setFont("Helvetica", 9.4)
    footer_text = contact_line or url.replace("https://", "").replace("http://", "")
    for i, line in enumerate(_wrap_lines(footer_text, footer_w - q_size - 18 * mm, "Helvetica", 9.4)[:2]):
        c.drawString(footer_x + 5 * mm, footer_y + 11 * mm - i * 4.2 * mm, line)

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _make_business_cards_pdf_legacy_unused(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    colors = _brand_colors(str(listing.get("plan") or "standard"))
    margin_x = 12 * mm
    margin_y = 14 * mm
    gap_x = 7 * mm
    gap_y = 6 * mm
    card_w = (W - 2 * margin_x - gap_x) / 2
    card_h = (H - 2 * margin_y - 4 * gap_y) / 5
    url = _public_listing_url(request, listing.get("slug") or "")
    contact_line = _safe_contact_line(listing)
    area_line = f"{listing.get('area','')} · {listing.get('city','')}".strip(" ·")
    sig_title, _, _ = _get_signature_dish(listing, lang)
    photo = _signature_image_path(listing)

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")

    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    for row in range(5):
        for col in range(2):
            x = margin_x + col * (card_w + gap_x)
            y = H - margin_y - (row + 1) * card_h - row * gap_y
            c.setFillColorRGB(1, 1, 1)
            c.setStrokeColorRGB(*colors["line"])
            c.setLineWidth(1)
            c.roundRect(x, y, card_w, card_h, 4 * mm, stroke=1, fill=1)
            top_h = 12 * mm
            c.setFillColorRGB(*flyer_violet_light)
            c.roundRect(x, y + card_h - top_h, card_w, top_h, 4 * mm, stroke=0, fill=1)
            c.setFillColorRGB(*colors["accent"])
            c.rect(x, y + card_h - 2 * mm, card_w, 2 * mm, stroke=0, fill=1)
            c.setFillColorRGB(*colors["ink"])
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x + 4 * mm, y + card_h - 7.5 * mm, str(listing.get("name") or "Kitchen")[:28])
            if area_line:
                c.setFillColorRGB(*colors["muted"])
                c.setFont("Helvetica", 7.2)
                c.drawString(x + 4 * mm, y + card_h - 11.2 * mm, area_line[:34])

            photo_x = x + 4 * mm
            photo_y = y + 4 * mm
            photo_w = 20 * mm
            photo_h = card_h - top_h - 8 * mm
            if _draw_cover_photo(c, photo, photo_x, photo_y, photo_w, photo_h):
                c.setStrokeColorRGB(*colors["line"])
                c.roundRect(photo_x, photo_y, photo_w, photo_h, 3 * mm, stroke=1, fill=0)
            else:
                c.setFillColorRGB(*flyer_violet_light)
                c.roundRect(photo_x, photo_y, photo_w, photo_h, 3 * mm, stroke=0, fill=1)

            qr_size = 16 * mm
            qx = x + card_w - qr_size - 4 * mm
            qy = y + 5 * mm
            c.setFillColorRGB(1, 1, 1)
            c.roundRect(qx - 1.4 * mm, qy - 1.4 * mm, qr_size + 2.8 * mm, qr_size + 2.8 * mm, 2 * mm, stroke=0, fill=1)
            c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask="auto")

            text_x = photo_x + photo_w + 4 * mm
            text_right = qx - 3 * mm
            text_w = max(20, text_right - text_x)
            c.setFillColorRGB(*colors["ink"])
            c.setFont("Helvetica-Bold", 9.4)
            c.drawString(text_x, y + 27 * mm, (sig_title or str(listing.get("name") or "Kitchen"))[:26])
            c.setFillColorRGB(*colors["muted"])
            c.setFont("Helvetica", 7)
            meta_y = y + 22 * mm
            meta_lines = []
            if contact_line:
                meta_lines.extend(_wrap_lines(contact_line, text_w, "Helvetica", 7)[:1])
            meta_lines.extend(_wrap_lines(url.replace("http://","").replace("https://",""), text_w, "Helvetica", 7)[:1])
            for line in meta_lines[:2]:
                c.drawString(text_x, meta_y, line)
                meta_y -= 3.8 * mm
            _draw_badge(c, text_x, y + 10 * mm, "SCAN MENU" if lang == "en" else "SKANN MENY", colors["accent"], font_size=6.6, h=6.2 * mm, pad_x=2.8 * mm)

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _make_gift_card_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    colors = _brand_colors(str(listing.get("plan") or "standard"))
    url = _public_listing_url(request, listing.get("slug") or "")
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")
    hero = _resolve_public_image_path(str(listing.get("hero_image") or ""))
    sig = _signature_image_path(listing)

    c.setFillColorRGB(0.97, 0.97, 0.98)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    outer_x = 18 * mm
    outer_y = 48 * mm
    outer_w = W - 36 * mm
    outer_h = 110 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*colors["line"])
    c.setLineWidth(1)
    c.roundRect(outer_x, outer_y, outer_w, outer_h, 7 * mm, stroke=1, fill=1)

    left_w = outer_w * 0.42
    if not _draw_cover_photo(c, hero or sig, outer_x, outer_y, left_w, outer_h):
        c.setFillColorRGB(*colors["accent2"])
        c.roundRect(outer_x, outer_y, left_w, outer_h, 7 * mm, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFillAlpha(0.18)
    c.roundRect(outer_x, outer_y, left_w, outer_h, 7 * mm, stroke=0, fill=1)
    c.setFillAlpha(1)

    right_x = outer_x + left_w + 6 * mm
    right_w = outer_w - left_w - 12 * mm
    _draw_badge(c, right_x, outer_y + outer_h - 14 * mm, "GIFT CARD" if lang == "en" else "GAVEKORT", colors["accent"], font_size=8)
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica-Bold", 24)
    c.drawString(right_x, outer_y + outer_h - 26 * mm, str(listing.get("name") or "Kitchen")[:24])
    c.setFillColorRGB(*colors["muted"])
    c.setFont("Helvetica", 11)
    c.drawString(right_x, outer_y + outer_h - 33 * mm, "A thoughtful local food gift" if lang == "en" else "En profesjonell lokal matgave")

    labels = ["To" if lang == "en" else "Til", "From" if lang == "en" else "Fra", "Value" if lang == "en" else "Beløp"]
    line_y = outer_y + outer_h - 48 * mm
    for i, lab in enumerate(labels):
        yy = line_y - i * 16 * mm
        c.setFillColorRGB(*colors["muted"])
        c.setFont("Helvetica-Bold", 9)
        c.drawString(right_x, yy + 3 * mm, lab)
        c.setStrokeColorRGB(*colors["line"])
        c.setLineWidth(0.9)
        c.line(right_x, yy, right_x + right_w - 50 * mm, yy)

    message = "Scan menu to redeem online." if lang == "en" else "Skann menyen for å løse inn digitalt."
    c.setFillColorRGB(*colors["ink"])
    c.setFont("Helvetica", 10.8)
    msg_y = outer_y + 16 * mm
    for line in _wrap_lines(message, right_w - 52 * mm, "Helvetica", 9.2)[:2]:
        c.drawString(right_x, msg_y, line)
        msg_y += 4.6 * mm

    qr_size = 28 * mm
    qx = outer_x + outer_w - qr_size - 9 * mm
    qy = outer_y + 12 * mm
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(qx - 2 * mm, qy - 2 * mm, qr_size + 4 * mm, qr_size + 4 * mm, 3 * mm, stroke=0, fill=1)
    c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask="auto")
    c.setFillColorRGB(*colors["muted"])
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(qx + qr_size / 2, qy - 4.5 * mm, "Scan to order" if lang == "en" else "Skann for å bestille")

    c.setStrokeColorRGB(*colors["line"])
    c.line(outer_x, outer_y - 6 * mm, outer_x + outer_w, outer_y - 6 * mm)
    c.setFillColorRGB(*colors["muted"])
    c.setFont("Helvetica", 8.2)
    c.drawString(outer_x, outer_y - 11 * mm, _safe_contact_line(listing)[:70])
    c.drawRightString(outer_x + outer_w, outer_y - 11 * mm, url[:78])

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _make_promo_cards_pdf(listing: dict, request: Request, lang: str = "en") -> BytesIO:
    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    colors = _brand_colors(str(listing.get("plan") or "standard"))
    url = _public_listing_url(request, listing.get("slug") or "")
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=5, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(ink_color or "#161616"), back_color=(bg_color or "#f7f1e8")).convert("RGB")
    title = str(listing.get("name") or "Kitchen")
    prompts = [
        ("Order again" if lang == "en" else "Bestill igjen", "Fast local pickup" if lang == "en" else "Rask lokal henting"),
        ("Share with a friend" if lang == "en" else "Del med en venn", "A kitchen worth trying" if lang == "en" else "Et kjøkken verdt å prøve"),
        ("Office lunch" if lang == "en" else "Kontorlunsj", "Simple food for teams" if lang == "en" else "Enkel mat for team"),
        ("Pickup made easy" if lang == "en" else "Enkel henting", "Scan and view the menu" if lang == "en" else "Skann og se menyen"),
        ("Food by request" if lang == "en" else "Mat på bestilling", "Fresh local dishes" if lang == "en" else "Ferske lokale retter"),
        ("Gift a meal" if lang == "en" else "Gi bort et måltid", "Perfect for someone nearby" if lang == "en" else "Perfekt for noen i nærheten"),
        ("New customer" if lang == "en" else "Ny kunde", "Start with the menu" if lang == "en" else "Start med menyen"),
        ("Neighborhood favorite" if lang == "en" else "Nabolagsfavoritt", "Made with care" if lang == "en" else "Laget med omtanke"),
    ]
    photo_paths = _listing_photo_paths(listing) or []

    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    margin = 12 * mm
    gap = 6 * mm
    card_w = (W - 2 * margin - gap) / 2
    card_h = (H - 2 * margin - 3 * gap) / 4
    idx = 0
    for row in range(4):
        for col in range(2):
            x = margin + col * (card_w + gap)
            y = H - margin - (row + 1) * card_h - row * gap
            headline, sub = prompts[idx]
            photo = photo_paths[idx % len(photo_paths)] if photo_paths else None
            idx += 1
            c.setFillColorRGB(1, 1, 1)
            c.setStrokeColorRGB(*colors["line"])
            c.roundRect(x, y, card_w, card_h, 4 * mm, stroke=1, fill=1)
            photo_w = 24 * mm
            if _draw_cover_photo(c, photo, x, y, photo_w, card_h):
                c.setFillColorRGB(0, 0, 0)
                c.setFillAlpha(0.08)
                c.rect(x, y, photo_w, card_h, stroke=0, fill=1)
                c.setFillAlpha(1)
            else:
                c.setFillColorRGB(*colors["accent2"])
                c.roundRect(x, y, photo_w, card_h, 4 * mm, stroke=0, fill=1)
            c.setFillColorRGB(*colors["accent"])
            c.rect(x + photo_w, y + card_h - 2 * mm, card_w - photo_w, 2 * mm, stroke=0, fill=1)
            tx = x + photo_w + 4 * mm
            _draw_badge(c, tx, y + card_h - 11 * mm, title[:18], colors["accent"], font_size=7, h=6.5 * mm, pad_x=3 * mm)
            c.setFillColorRGB(*colors["ink"])
            c.setFont("Helvetica-Bold", 12)
            c.drawString(tx, y + card_h - 18 * mm, headline[:22])
            c.setFillColorRGB(*colors["muted"])
            c.setFont("Helvetica", 8.5)
            for n, line in enumerate(_wrap_lines(sub, card_w - photo_w - 34 * mm, "Helvetica", 8.5)[:2]):
                c.drawString(tx, y + card_h - 24 * mm - n * 4.3 * mm, line)
            qr_size = 16 * mm
            qx = x + card_w - qr_size - 4 * mm
            qy = y + 4.5 * mm
            c.setFillColorRGB(1, 1, 1)
            c.roundRect(qx - 1.4 * mm, qy - 1.4 * mm, qr_size + 2.8 * mm, qr_size + 2.8 * mm, 2 * mm, stroke=0, fill=1)
            c.drawImage(ImageReader(qr_img), qx, qy, width=qr_size, height=qr_size, mask="auto")
            c.setFillColorRGB(*colors["muted"])
            c.setFont("Helvetica-Bold", 7)
            c.drawString(tx, y + 9 * mm, "Scan menu" if lang == "en" else "Skann meny")
            c.setFont("Helvetica", 6.8)
            c.drawString(tx, y + 5 * mm, url[:24])
    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


def _pdf_stream_response(pdf: BytesIO, filename: str, download: int = 1):
    disposition = 'attachment' if int(download or 0) == 1 else 'inline'
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'}
    )


@app.get("/api/owner/{token}/flyer.pdf")
def owner_flyer_pdf(token: str, request: Request, lang: str = "en", download: int = 1):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'
    pdf = _make_flyer_pdf(listing, request, lang=lang)
    fn = f"{listing.get('slug')}-flyer-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.get("/api/owner/{token}/flyer2.pdf")
def owner_flyer2_pdf(
    token: str,
    request: Request,
    lang: str = "en",
    download: int = 1,
    headline: str | None = None,
    support: str | None = None,
    accent: str | None = None,
    focal_x: float | None = None,
    focal_y: float | None = None,
    zoom: float | None = None,
):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'

    working_listing = dict(listing or {})
    lang_key = 'no' if lang == 'no' else 'en'

    if headline is not None:
        existing = working_listing.get("flyer_headline") if isinstance(working_listing.get("flyer_headline"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = headline
        working_listing["flyer_headline"] = existing
    if support is not None:
        existing = working_listing.get("flyer_support") if isinstance(working_listing.get("flyer_support"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = support
        working_listing["flyer_support"] = existing
    if accent is not None and re.fullmatch(r"#[0-9a-fA-F]{6}", accent or ""):
        working_listing["flyer_accent"] = accent
    if focal_x is not None:
        working_listing["flyer_image_focal_x"] = max(0, min(100, float(focal_x)))
    if focal_y is not None:
        working_listing["flyer_image_focal_y"] = max(0, min(100, float(focal_y)))
    if zoom is not None:
        working_listing["flyer_image_zoom"] = max(100, min(200, float(zoom)))

    try:
        pdf = _make_flyer2_pdf(working_listing, request, lang=lang)
    except Exception:
        safe_listing = dict(working_listing or {})
        safe_listing["contact"] = safe_listing.get("contact") if isinstance(safe_listing.get("contact"), dict) else {}
        safe_listing["flyer_image_focal_x"] = max(0, min(100, float(safe_listing.get("flyer_image_focal_x") or 50)))
        safe_listing["flyer_image_focal_y"] = max(0, min(100, float(safe_listing.get("flyer_image_focal_y") or 50)))
        safe_listing["flyer_image_zoom"] = max(100, min(200, float(safe_listing.get("flyer_image_zoom") or 100)))
        pdf = _make_flyer2_pdf(safe_listing, request, lang=lang)
    fn = f"{listing.get('slug')}-poster2-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.get("/api/owner/{token}/flyer3.pdf")
def owner_flyer3_pdf(
    token: str,
    request: Request,
    lang: str = "en",
    download: int = 1,
    headline: str | None = None,
    support: str | None = None,
    accent: str | None = None,
    focal_x: float | None = None,
    focal_y: float | None = None,
    zoom: float | None = None,
):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'

    working_listing = dict(listing or {})
    lang_key = 'no' if lang == 'no' else 'en'

    if headline is not None:
        existing = working_listing.get("poster3_headline") if isinstance(working_listing.get("poster3_headline"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = headline
        working_listing["poster3_headline"] = existing
    if support is not None:
        existing = working_listing.get("poster3_support") if isinstance(working_listing.get("poster3_support"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = support
        working_listing["poster3_support"] = existing
    if accent is not None and re.fullmatch(r"#[0-9a-fA-F]{6}", accent or ""):
        working_listing["poster3_accent"] = accent
    if focal_x is not None:
        working_listing["poster3_image_focal_x"] = max(0, min(100, float(focal_x)))
    if focal_y is not None:
        working_listing["poster3_image_focal_y"] = max(0, min(100, float(focal_y)))
    if zoom is not None:
        working_listing["poster3_image_zoom"] = max(100, min(200, float(zoom)))

    try:
        pdf = _make_flyer3_pdf(working_listing, request, lang=lang)
    except Exception:
        safe_listing = dict(working_listing or {})
        safe_listing["contact"] = safe_listing.get("contact") if isinstance(safe_listing.get("contact"), dict) else {}
        safe_listing["poster3_image_focal_x"] = max(0, min(100, float(safe_listing.get("poster3_image_focal_x") or safe_listing.get("flyer_image_focal_x") or 50)))
        safe_listing["poster3_image_focal_y"] = max(0, min(100, float(safe_listing.get("poster3_image_focal_y") or safe_listing.get("flyer_image_focal_y") or 50)))
        safe_listing["poster3_image_zoom"] = max(100, min(200, float(safe_listing.get("poster3_image_zoom") or safe_listing.get("flyer_image_zoom") or 100)))
        pdf = _make_flyer3_pdf(safe_listing, request, lang=lang)
    fn = f"{listing.get('slug')}-poster3-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)

@app.get("/api/owner/{token}/flyer4.pdf")
def owner_flyer4_pdf(
    token: str,
    request: Request,
    lang: str = "en",
    download: int = 1,
    headline: str | None = None,
    support: str | None = None,
    accent: str | None = None,
    top_focal_x: float | None = None,
    top_focal_y: float | None = None,
    top_zoom: float | None = None,
    left_focal_x: float | None = None,
    left_focal_y: float | None = None,
    left_zoom: float | None = None,
    right_focal_x: float | None = None,
    right_focal_y: float | None = None,
    right_zoom: float | None = None,
    title_font_size: float | None = None,
):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'

    working_listing = dict(listing or {})
    lang_key = 'no' if lang == 'no' else 'en'

    if headline is not None:
        existing = working_listing.get("poster4_headline") if isinstance(working_listing.get("poster4_headline"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = headline
        working_listing["poster4_headline"] = existing
    if support is not None:
        existing = working_listing.get("poster4_support") if isinstance(working_listing.get("poster4_support"), dict) else {}
        existing = dict(existing)
        existing[lang_key] = support
        working_listing["poster4_support"] = existing
    if accent is not None and re.fullmatch(r"#[0-9a-fA-F]{6}", accent or ""):
        working_listing["poster4_accent"] = accent

    def _apply_flyer4_crop(key: str, val: float | None, lo: float, hi: float):
        if val is None:
            return
        try:
            working_listing[key] = max(lo, min(hi, float(val)))
        except Exception:
            return

    _apply_flyer4_crop("poster4_top_image_focal_x", top_focal_x, 0.0, 100.0)
    _apply_flyer4_crop("poster4_top_image_focal_y", top_focal_y, 0.0, 100.0)
    _apply_flyer4_crop("poster4_top_image_zoom", top_zoom, 100.0, 200.0)
    _apply_flyer4_crop("poster4_left_image_focal_x", left_focal_x, 0.0, 100.0)
    _apply_flyer4_crop("poster4_left_image_focal_y", left_focal_y, 0.0, 100.0)
    _apply_flyer4_crop("poster4_left_image_zoom", left_zoom, 100.0, 200.0)
    _apply_flyer4_crop("poster4_right_image_focal_x", right_focal_x, 0.0, 100.0)
    _apply_flyer4_crop("poster4_right_image_focal_y", right_focal_y, 0.0, 100.0)
    _apply_flyer4_crop("poster4_right_image_zoom", right_zoom, 100.0, 200.0)
    _apply_flyer4_crop("poster4_title_font_size", title_font_size, 12.0, 30.0)

    pdf = _make_flyer4_pdf(working_listing, request, lang=lang)
    fn = f"{listing.get('slug')}-poster4-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.get("/api/owner/{token}/business-cards.pdf")
def owner_business_cards_pdf(token: str, request: Request, lang: str = "en", download: int = 1, layout: str = "sheet"):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'
    pdf = _make_business_cards_pdf(listing, request, lang=lang, layout=layout)
    fn = f"{listing.get('slug')}-business-cards-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.get("/api/owner/{token}/thank-you-cards.pdf")
def owner_thank_you_cards_pdf(token: str, request: Request, lang: str = "en", download: int = 1, layout: str = "sheet"):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'
    pdf = _make_thank_you_cards_pdf(listing, request, lang=lang, layout=layout)
    fn = f"{listing.get('slug')}-thank-you-cards-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.get("/api/owner/{token}/gift-card.pdf")
def owner_gift_card_pdf(token: str, request: Request, lang: str = "en", download: int = 1):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'
    pdf = _make_gift_card_pdf(listing, request, lang=lang)
    fn = f"{listing.get('slug')}-gift-card-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.get("/api/owner/{token}/promo-cards.pdf")
def owner_promo_cards_pdf(token: str, request: Request, lang: str = "en", download: int = 1):
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    _require_plan(listing, 'standard')
    lang = (lang or 'en').lower().strip()
    if lang not in ('en', 'no'):
        lang = 'en'
    pdf = _make_promo_cards_pdf(listing, request, lang=lang)
    fn = f"{listing.get('slug')}-promo-cards-{lang}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


def _origin_from_request(request: Request) -> str:
    # In staging/production, use the configured public URL so Stripe redirects never
    # point to an internal host. In local development, prefer the browser origin.
    if runtime_config.public_base_url:
        return runtime_config.public_base_url.rstrip('/')
    origin = (request.headers.get('origin') or '').strip()
    if origin:
        return origin.rstrip('/')
    return str(request.base_url).rstrip('/')


def _stripe_price_id(plan: str, billing: str, country: str = "", currency: str = "") -> str:
    plan = (plan or 'basic').lower().strip()
    billing = (billing or 'monthly').lower().strip()
    if billing == 'annual':
        billing = 'yearly'

    # normalize legacy name
    if plan in ('premium', 'standard'):
        plan = 'business'
    if plan == 'plus':
        plan = 'growth'
    if plan not in STRIPE_PLAN_KEYS:
        plan = 'basic'
    if billing not in STRIPE_BILLING_KEYS:
        billing = 'monthly'

    cur = (currency or _stripe_country_to_currency(country)).upper().strip()
    pid = _stripe_currency_price_id(plan, billing, cur)

    # Fallback to older global env names so existing local/test setups keep working.
    if not pid:
        pid = _stripe_global_price_ids().get(f"{plan}_{billing}", "")

    if not pid:
        raise HTTPException(
            status_code=500,
            detail=f'Stripe price id not configured for {plan}/{billing}/{cur}'
        )
    return pid


def _normalize_plan_key(plan: str) -> str:
    p = (plan or 'basic').lower().strip()
    if p in ('premium', 'standard'):
        return 'business'
    if p == 'plus':
        return 'growth'
    if p not in STRIPE_PLAN_KEYS:
        raise HTTPException(status_code=400, detail=f'Unsupported plan: {plan}')
    return p


def _normalize_billing_key(billing: str) -> str:
    b = (billing or 'monthly').lower().strip()
    if b == 'annual':
        b = 'yearly'
    if b not in STRIPE_BILLING_KEYS:
        raise HTTPException(status_code=400, detail=f'Unsupported billing interval: {billing}')
    return b


def _normalize_checkout_country(country: str) -> str:
    c = (country or 'NO').upper().strip()
    if c == 'UK':
        c = 'GB'
    if c not in STRIPE_COUNTRY_CURRENCY:
        raise HTTPException(status_code=400, detail=f'Unsupported checkout country: {country}')
    return c


def _normalize_checkout_payload(payload: dict, item: dict) -> dict:
    pld = payload or {}
    plan = _normalize_plan_key(str(pld.get('plan') or item.get('plan') or 'basic'))
    billing = _normalize_billing_key(str(pld.get('billing') or item.get('billing') or 'monthly'))
    country = _normalize_checkout_country(str(pld.get('country') or item.get('country') or 'NO'))
    expected_currency = _stripe_country_to_currency(country).upper().strip()
    requested_currency = str(pld.get('currency') or expected_currency).upper().strip()
    if requested_currency and requested_currency != expected_currency:
        raise HTTPException(
            status_code=400,
            detail=f'Currency mismatch for {country}: expected {expected_currency}, got {requested_currency}'
        )
    return {
        'plan': plan,
        'billing': billing,
        'country': country,
        'currency': expected_currency,
        'discount_code': str(pld.get('discount_code') or '').strip().upper(),
        'referred_by_code': str(pld.get('referred_by_code') or '').strip().upper(),
        'referral_credit_to_apply': str(pld.get('referral_credit_to_apply') or '').strip(),
    }


def _stripe_public_status_for_admin() -> dict:
    cfg = _stripe_config_snapshot()
    # Do not expose actual secrets or price id values. This is only readiness metadata.
    return {
        "ok": True,
        "mode": cfg.get("mode"),
        "secret_key_set": cfg.get("secret_key_set"),
        "webhook_secret_set": cfg.get("webhook_secret_set"),
        "configured_by_currency": cfg.get("configured_by_currency"),
        "missing_by_currency": cfg.get("missing_by_currency"),
        "all_supported_currency_prices_ready": cfg.get("all_supported_currency_prices_ready"),
        "supported_currencies": list(STRIPE_CURRENCY_MARKETS),
        "supported_plans": list(STRIPE_PLAN_KEYS),
        "supported_billing": list(STRIPE_BILLING_KEYS),
    }




@app.get("/api/cuisines")
def get_cuisines():
    return {"cuisines": CUISINES}


@app.get("/api/listings")
def list_listings(
    q: Optional[str] = None,
    cuisine: Optional[str] = None,
    country: Optional[str] = None,
    has_group: Optional[bool] = None,
    has_family: Optional[bool] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = 40.0,
):
    items = db_list_listings(
        q=q,
        cuisine=cuisine,
        country=country,
        note_weekend=None,
        has_group=has_group,
        has_family=has_family,
        lat=lat,
        lng=lng,
        radius_km=float(radius_km or 40.0),
        include_drafts=False,
    )

    out = [
        {
            "id": i.get("id"),
            "slug": i.get("slug"),
            "name": i.get("name"),
            "area": i.get("area"),
            "city": i.get("city"),
            "postcode": i.get("postcode", ""),
            "country": i.get("country"),
            "cuisines": i.get("cuisines", []),
            "badges": i.get("badges", []),
            "from_price": i.get("from_price"),
            "currency": i.get("currency"),
            "hero_image": i.get("hero_image"),
            # Explore (feed) image crop position. 0..100 (y-axis), default 50.
            "explore_focal_y": i.get("explore_focal_y"),
            # Explore (feed) image zoom. Percent (100..170), default 120.
            "explore_zoom": i.get("explore_zoom"),
            "intro": i.get("intro", {}),
            "plan": i.get("plan", "basic"),
            "distance_km": i.get("distance_km"),
            # Neutral public platform-history marker. Displayed as
            # "Listed on RiceMap24 since Month Year" on cards and kitchen pages.
            "joined_at": i.get("joined_at") or i.get("created_at"),
            "created_at": i.get("created_at"),
            # Public coordinates for map view.
            # NOTE: We intentionally round to keep it approximate (privacy-friendly).
            "lat": (round(float(i.get("lat")), 2) if i.get("lat") is not None else None),
            "lng": (round(float(i.get("lng")), 2) if i.get("lng") is not None else None),
        }
        for i in items
    ]

    return {"items": out, "count": len(out)}


@app.get("/api/map/listings")
def map_listings(
    cuisine: Optional[str] = None,
    country: Optional[str] = None,
    has_group: Optional[bool] = None,
    has_family: Optional[bool] = None,
):
    """Minimal listing payload for the public map.

    Key idea (Airbnb-ish): show ALL live kitchens on the map by default,
    optionally filtered by the structured filters (cuisine/etc).

    We intentionally do NOT support free-text q here — q is used for list search
    + centering (via /api/geocode).
    """
    items = db_list_listings(
        q=None,
        cuisine=cuisine,
        country=country,
        note_weekend=None,
        has_group=has_group,
        has_family=has_family,
        lat=None,
        lng=None,
        radius_km=0.0,
        include_drafts=False,
    )

    out = [
        {
            "id": i.get("id"),
            "slug": i.get("slug"),
            "name": i.get("name"),
            "area": i.get("area"),
            "city": i.get("city"),
            "country": i.get("country"),
            "cuisines": i.get("cuisines", []),
            "badges": i.get("badges", []),
            "hero_image": i.get("hero_image"),
            "explore_focal_y": i.get("explore_focal_y"),
            "explore_zoom": i.get("explore_zoom"),
            "plan": i.get("plan", "basic"),
            "lat": (round(float(i.get("lat")), 2) if i.get("lat") is not None else None),
            "lng": (round(float(i.get("lng")), 2) if i.get("lng") is not None else None),
        }
        for i in items
    ]
    return {"items": out, "count": len(out)}


def _country_to_iso2(country: Optional[str]) -> str:
    """Return ISO-3166 alpha-2 for common country names/codes.

    Nominatim countrycodes requires ISO2. Passing values such as "Norway" or
    "United States" makes geocoding fail, which also makes new kitchens drop
    out of map/nearest search.
    """
    c = (country or "").strip().lower()
    if not c:
        return ""
    if len(c) == 2 and c.isalpha():
        return c
    aliases = {
        "norway":"no", "norge":"no",
        "sweden":"se", "sverige":"se",
        "denmark":"dk", "danmark":"dk",
        "finland":"fi",
        "united states":"us", "usa":"us", "us":"us", "america":"us",
        "united kingdom":"gb", "uk":"gb", "great britain":"gb", "england":"gb",
        "germany":"de", "deutschland":"de",
        "france":"fr", "spain":"es", "italy":"it", "netherlands":"nl",
        "portugal":"pt", "ireland":"ie", "switzerland":"ch",
        "thailand":"th", "philippines":"ph", "filipino":"ph",
        "vietnam":"vn", "viet nam":"vn", "china":"cn",
        "indonesia":"id", "korea":"kr", "south korea":"kr",
    }
    return aliases.get(c, "")


def _fallback_city_geocode(q: str, country: Optional[str]) -> Optional[dict]:
    """Small offline fallback so staging does not depend fully on Nominatim.

    This is intentionally approximate and city-level only. It is enough for map
    placement and nearest sorting when external geocoding is unavailable.
    """
    text = f"{q or ''} {country or ''}".lower()
    points = {
        "oslo": (59.9139, 10.7522), "fredrikstad": (59.2205, 10.9347),
        "sarpsborg": (59.2839, 11.1096), "moss": (59.4340, 10.6577),
        "bergen": (60.3913, 5.3221), "trondheim": (63.4305, 10.3951),
        "stavanger": (58.9700, 5.7331), "tromsø": (69.6492, 18.9553),
        "stockholm": (59.3293, 18.0686), "gothenburg": (57.7089, 11.9746),
        "malmö": (55.6050, 13.0038), "copenhagen": (55.6761, 12.5683),
        "københavn": (55.6761, 12.5683), "helsinki": (60.1699, 24.9384),
        "london": (51.5072, -0.1276), "new york": (40.7128, -74.0060),
        "los angeles": (34.0522, -118.2437), "chicago": (41.8781, -87.6298),
        "bangkok": (13.7563, 100.5018), "manila": (14.5995, 120.9842),
        "hanoi": (21.0278, 105.8342), "ho chi minh": (10.8231, 106.6297),
    }
    for name, (lat, lng) in points.items():
        if name in text:
            return {"ok": True, "lat": lat, "lng": lng, "display_name": name.title(), "cached": False, "provider": "fallback_city"}
    return None


@app.get("/api/geocode")
def geocode(q: str, country: Optional[str] = None):
    """Geocode a location string (city/postcode) to lat/lng.

    Uses OpenStreetMap Nominatim with ISO2 country codes and stores a simple
    cache. Falls back to a small internal city list if the external lookup fails.
    """
    q_clean = (q or "").strip()
    if not q_clean:
        return {"ok": False}

    country_clean = (country or "").strip().lower()
    country_iso2 = _country_to_iso2(country_clean)
    key = f"{q_clean.lower()}|{country_iso2 or country_clean}"

    cached = geocache_get(key)
    if cached and cached.get("lat") is not None and cached.get("lng") is not None:
        return {
            "ok": True,
            "lat": cached.get("lat"),
            "lng": cached.get("lng"),
            "display_name": cached.get("display_name"),
            "cached": True,
            "provider": cached.get("provider", "cache"),
        }

    params = {"q": q_clean, "format": "jsonv2", "limit": 1}
    if country_iso2:
        params["countrycodes"] = country_iso2

    try:
        with httpx.Client(timeout=6.5, headers={"User-Agent": "RiceMap24MVP/1.0 (local dev)"}) as client:
            r = client.get("https://nominatim.openstreetmap.org/search", params=params)
            r.raise_for_status()
            data = r.json()
    except Exception:
        data = []

    if data:
        hit = data[0]
        try:
            lat_v = float(hit.get("lat"))
            lng_v = float(hit.get("lon"))
            display = hit.get("display_name") or q_clean
            geocache_set(key, display, lat_v, lng_v, provider="nominatim")
            return {"ok": True, "lat": lat_v, "lng": lng_v, "display_name": display, "cached": False, "provider": "nominatim"}
        except Exception:
            pass

    fallback = _fallback_city_geocode(q_clean, country_clean)
    if fallback:
        try:
            geocache_set(key, fallback.get("display_name") or q_clean, float(fallback["lat"]), float(fallback["lng"]), provider="fallback_city")
        except Exception:
            pass
        return fallback
    return {"ok": False}


@app.get("/api/listings/{slug}")
def get_listing(slug: str):
    item = get_by_slug(slug)
    if item and int(item.get("published", 1)) == 1 and int(item.get("plan_active", 1)) == 1:
        return item
    raise HTTPException(status_code=404, detail="Listing not found")

# --- Premium: Customers (CRM light) -------------------------------------------

def _resolve_owner_listing(token: str) -> dict:
    """Resolve token to listing.

    Token is normally preview_token, but for demo convenience we also accept a
    published slug.
    """
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Preview token not found")
    if token == listing.get("slug") and int(listing.get("published", 0)) != 1:
        raise HTTPException(status_code=404, detail="Preview token not found")
    return listing


@app.get("/api/owner/{token}/announcements")
def owner_announcements(token: str):
    listing = _resolve_owner_listing(token)
    items = list_active_owner_announcements(int(listing["id"]), str(listing.get("plan") or "basic"))
    return {"items": items}


@app.get("/api/owner/{token}/customers")
def owner_list_customers(token: str, q: str = ""):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    items = list_customers(int(listing["id"]), q=q)
    return {"items": items, "count": len(items)}


@app.post("/api/owner/{token}/settings")
async def owner_update_settings(token: str, payload: dict):
    """Owner settings patch (MVP): currently only currency."""
    listing = _resolve_owner_listing(token)
    currency = str((payload or {}).get("currency") or "").strip().upper()
    allowed_currencies = {"NOK", "SEK", "DKK", "EUR", "GBP", "USD", "CHF"}
    if currency not in allowed_currencies:
        raise HTTPException(status_code=400, detail="currency must be NOK, SEK, DKK, EUR, GBP, USD or CHF")
    try:
        updated = set_listing_currency(int(listing["id"]), currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "listing": updated}


@app.post("/api/owner/{token}/save")
async def owner_save_listing(token: str, payload: dict):
    """Save listing changes using the owner token (stable endpoint for dashboard)."""
    listing = _resolve_owner_listing(token)
    listing_id = int(listing["id"])
    try:
        update_draft(listing_id, payload or {})
    except KeyError:
        raise HTTPException(status_code=404, detail="Listing not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}




@app.post("/api/owner/{token}/delete")
async def owner_delete_listing_account(token: str, payload: dict, session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME)):
    """Owner-requested soft deletion. Requires explicit DELETE confirmation."""
    listing = _resolve_owner_listing(token)
    confirm = str((payload or {}).get("confirm") or "").strip()
    if confirm != "DELETE":
        raise HTTPException(status_code=400, detail="Type DELETE to confirm deletion")
    try:
        deleted = soft_delete_listing_by_owner(int(listing["id"]))
    except KeyError:
        raise HTTPException(status_code=404, detail="Listing not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    response = JSONResponse({"ok": True, "deleted": True, "listing": deleted})
    try:
        if session_token:
            revoke_app_session(session_token)
        response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    except Exception:
        pass
    return response


@app.post("/api/owner/{token}/publish")
async def owner_publish_listing(token: str, payload: dict):
    """Owner-controlled publishing. Paid/active subscription is required before public visibility."""
    listing = _resolve_owner_listing(token)
    listing_id = int(listing["id"])
    was_published = int(listing.get("published") or 0) == 1
    try:
        updated = set_listing_publication(listing_id, 1 if (payload or {}).get("published") else 0)
    except KeyError:
        raise HTTPException(status_code=404, detail="Listing not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        is_published = int(updated.get("published", 0)) == 1
        if is_published and not was_published:
            _queue_owner_template_once(updated, "kitchen_published", "kitchen_published")
    except Exception:
        pass
    return {"ok": True, "published": int(updated.get("published", 0))}


def _dish_key(m: dict) -> str:
    # Keep in sync with client normalizeDishKey(). We prefer explicit dish_key.
    if isinstance(m, dict) and m.get("dish_key"):
        return str(m.get("dish_key"))
    name = ""
    try:
        nm = (m.get("name") or {}) if isinstance(m, dict) else {}
        if isinstance(nm, dict):
            name = str(nm.get("en") or nm.get("no") or "")
    except Exception:
        name = ""
    title = ""
    try:
        title = str(m.get("title") or "") if isinstance(m, dict) else ""
    except Exception:
        title = ""
    key = (name or title or "").strip().lower()
    return key


@app.post("/api/owner/{token}/dish_crop")
async def owner_patch_dish_crop(token: str, payload: dict):
    """Patch dish image crop (zoom + focal Y) for a dish group by dish_key.

    This avoids overwriting other listing edits by only modifying menu image crop fields.
    """
    listing = _resolve_owner_listing(token)
    listing_id = int(listing["id"])
    dish_key = str((payload or {}).get("dish_key") or "").strip()
    if not dish_key:
        raise HTTPException(status_code=400, detail="dish_key is required")
    try:
        focal_y = float((payload or {}).get("image_focal_y", 50))
    except Exception:
        focal_y = 50.0
    try:
        zoom = float((payload or {}).get("image_zoom", 120))
    except Exception:
        zoom = 120.0

    focal_y = max(0.0, min(100.0, focal_y))
    zoom = max(100.0, min(200.0, zoom))

    # Load latest listing JSON from DB and patch the menu.
    data = dict(listing)
    menu = data.get("menu") or []
    if not isinstance(menu, list):
        menu = []
    changed = False
    for m in menu:
        if not isinstance(m, dict):
            continue
        if _dish_key(m) == dish_key:
            m["image_focal_y"] = focal_y
            m["image_zoom"] = zoom
            changed = True

    if not changed:
        # Not fatal: allow saving even if key not found.
        return {"ok": True, "changed": False}

    data["menu"] = menu
    try:
        update_draft(listing_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "changed": True}


@app.post("/api/owner/{token}/customers")
async def owner_create_customer(token: str, payload: dict):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    # accept name/phone/email/tags/notes
    try:
        item = create_customer(int(listing["id"]), payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "item": item}


@app.put("/api/owner/{token}/customers/{customer_id}")
async def owner_update_customer(token: str, customer_id: int, payload: dict):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    try:
        item = update_customer(int(listing["id"]), int(customer_id), payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not item:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"ok": True, "item": item}


@app.delete("/api/owner/{token}/customers/{customer_id}")
def owner_delete_customer(token: str, customer_id: int):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    ok = delete_customer(int(listing["id"]), int(customer_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"ok": True}


@app.get("/api/owner/{token}/customers.csv")
def owner_customers_csv(token: str):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    items = list_customers(int(listing["id"]), q="")

    # CSV export
    output = BytesIO()
    # UTF-8 BOM helps Excel
    output.write(b'\xef\xbb\xbf')
    import io
    wrapper = io.TextIOWrapper(output, encoding="utf-8", newline="")
    writer = csv.writer(wrapper)
    writer.writerow(["customer_no", "name", "org_no", "phone", "email", "tags", "notes", "last_contacted_at", "created_at"])
    for it in items:
        tags = ", ".join(it.get("tags") or [])
        writer.writerow([
            it.get("customer_no") or "",
            it.get("name") or "",
            it.get("org_no") or "",
            it.get("phone") or "",
            it.get("email") or "",
            tags,
            it.get("notes") or "",
            it.get("last_contacted_at") or "",
            it.get("created_at") or "",
        ])
    wrapper.flush()
    data = output.getvalue()

    headers = {
        "Content-Disposition": f"attachment; filename=customers-{listing.get('slug')}.csv",
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(content=data, media_type="text/csv; charset=utf-8", headers=headers)




# --- Premium: Receipts (offline-friendly) ------------------------------------

def _safe_txt(v: Optional[str]) -> str:
    return (str(v or '').strip())


def _draw_kv_pair(c, x, y, k, v, ksize=9, vsize=10):
    c.setFillColorRGB(0.35, 0.38, 0.42)
    c.setFont("Helvetica", ksize)
    c.drawString(x, y, k)
    c.setFillColorRGB(0.08, 0.10, 0.12)
    c.setFont("Helvetica", vsize)
    c.drawString(x + 78, y, v)


def _make_receipt_pdf(listing: dict, receipt: dict, request: Request, lang: str = "en") -> BytesIO:
    """Create a simple A4 receipt PDF.

    This works even when payment happens outside the app (cash/Vipps/card).
    """
    lang = (lang or "en").lower().strip()
    if lang not in ("en", "no"):
        lang = "en"

    pdf = BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    W, H = A4
    margin = 16 * mm

    # Labels
    L = {
        "title_receipt": "Kvittering" if lang == "no" else "Receipt",
        "title_invoice": "Faktura" if lang == "no" else "Invoice",
        "seller": "Selger" if lang == "no" else "Seller",
        "buyer": "Kunde" if lang == "no" else "Buyer",
        "doc_no": "Nr" if lang == "no" else "No.",
        "issue_date": "Dato" if lang == "no" else "Issue date",
        "due_date": "Forfall" if lang == "no" else "Due date",
        "paid": "Betalt" if lang == "no" else "Paid",
        "payment": "Betalingsmåte" if lang == "no" else "Payment",
        "items": "Varer" if lang == "no" else "Items",
        "desc": "Beskrivelse" if lang == "no" else "Description",
        "amount": "Beløp" if lang == "no" else "Amount",
        "total": "Totalt" if lang == "no" else "Total",
        "note": "Notat" if lang == "no" else "Note",
        "generated": "Betaling håndteres utenfor RiceMap24" if lang == "no" else "Payment handled outside RiceMap24",
    }

    doc_type = (receipt.get("doc_type") or "receipt").lower()
    title = L["title_invoice"] if doc_type == "invoice" else L["title_receipt"]

    # Background
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Header
    c.setFillColorRGB(0.08, 0.10, 0.12)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(margin, H - margin - 8, title)

    c.setFillColorRGB(0.35, 0.38, 0.42)
    c.setFont("Helvetica", 10)
    # (header note removed)

    # Document meta
    y0 = H - margin - 28
    c.setLineWidth(0.7)
    c.setStrokeColorRGB(0.92, 0.93, 0.95)
    c.line(margin, y0, W - margin, y0)

    y = y0 - 14
    receipt_no = _safe_txt(receipt.get("receipt_no"))
    issue_date = _safe_txt(receipt.get("issue_date"))
    due_date = _safe_txt(receipt.get("due_date"))
    paid = bool(int(receipt.get("paid") or 0))
    paid_date = _safe_txt(receipt.get("paid_date"))
    payment_method = _safe_txt(receipt.get("payment_method"))

    _draw_kv_pair(c, margin, y, L["doc_no"], receipt_no)
    _draw_kv_pair(c, margin, y - 12, L["issue_date"], issue_date)
    if doc_type == "invoice" and due_date:
        _draw_kv_pair(c, margin, y - 24, L["due_date"], due_date)

    right_x = W - margin - 220
    _draw_kv_pair(c, right_x, y, L["paid"], ("Ja" if lang=="no" else "Yes") if paid else ("Nei" if lang=="no" else "No"))
    if paid and paid_date and paid_date != issue_date:
        _draw_kv_pair(c, right_x, y - 12, ("Betalt dato" if lang=="no" else "Paid date"), paid_date)
    if payment_method:
        _draw_kv_pair(c, right_x, y - 24, L["payment"], payment_method)

    # Seller / Buyer boxes
    box_y = y - 52
    box_h = 62
    box_w = (W - 2 * margin - 10) / 2

    def draw_box(x, title, lines):
        c.setStrokeColorRGB(0.90, 0.92, 0.94)
        c.setFillColorRGB(0.98, 0.98, 0.99)
        c.rect(x, box_y - box_h, box_w, box_h, stroke=1, fill=1)
        c.setFillColorRGB(0.08, 0.10, 0.12)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x + 10, box_y - 16, title)
        c.setFillColorRGB(0.35, 0.38, 0.42)
        c.setFont("Helvetica", 10)
        yy = box_y - 30
        for ln in lines[:3]:
            c.drawString(x + 10, yy, ln)
            yy -= 12

    seller_lines = [
        _safe_txt(listing.get("name")),
        f"{_safe_txt(listing.get('area'))} · {_safe_txt(listing.get('city'))}".strip(" ·"),
    ]
    seller_lines = [x for x in seller_lines if x]

    buyer_lines = [
        _safe_txt(receipt.get("buyer_name")),
        ("Org.nr " if lang=="no" else "Org. no ") + _safe_txt(receipt.get("buyer_org_no")) if _safe_txt(receipt.get("buyer_org_no")) else "",
        _safe_txt(receipt.get("buyer_email")) or _safe_txt(receipt.get("buyer_phone")),
    ]
    buyer_lines = [x for x in buyer_lines if x]

    draw_box(margin, L["seller"], seller_lines or ["-"])
    draw_box(margin + box_w + 10, L["buyer"], buyer_lines or ["-"])

    # Line item
    table_y = box_y - box_h - 18
    c.setFillColorRGB(0.08, 0.10, 0.12)
    c.setFont("Helvetica-Bold", 13)
    
    # Optional line items (stored as JSON string)
    items = []
    raw_items = receipt.get("items_json") or ""
    if raw_items:
        try:
            parsed = json.loads(raw_items) if isinstance(raw_items, str) else raw_items
            if isinstance(parsed, list):
                items = [x for x in parsed if isinstance(x, dict)]
        except Exception:
            items = []
    has_items = bool(items)
    c.drawString(margin, table_y, (L["items"] if has_items else L["desc"]))
    c.drawRightString(W - margin, table_y, L["amount"])

    c.setStrokeColorRGB(0.92, 0.93, 0.95)
    c.line(margin, table_y - 6, W - margin, table_y - 6)

    desc = _safe_txt(receipt.get("description"))
    note = _safe_txt(receipt.get("note"))
    currency = _safe_txt(receipt.get("currency"))
    amt = float(receipt.get("amount") or 0)

    money = f"{int(round(amt))} {currency}".strip() if currency else f"{int(round(amt))}"

    # Wrap description so longer free-text doesn't overflow

    def _wrap_text(s: str, max_w: float, font: str = "Helvetica", size: int = 11, max_lines: int = 3):
        s = (s or "").strip()
        if not s:
            return []
        words = s.split()
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if not cur or stringWidth(test, font, size) <= max_w:
                cur = test
            else:
                lines.append(cur)
                cur = w
                if len(lines) >= max_lines:
                    break
        if cur and len(lines) < max_lines:
            lines.append(cur)
        # If we likely truncated, add ellipsis
        if len(lines) == max_lines and len(words) > len(" ".join(lines).split()):
            if lines:
                if not lines[-1].endswith("…"):
                    lines[-1] = (lines[-1].rstrip('.') + "…")
        return lines


    # Table body
    left_max_w = (W - margin) - 120 - margin  # leave room for amount column
    c.setFillColorRGB(0.12, 0.14, 0.18)
    c.setFont("Helvetica", 11)

    y_desc = table_y - 22

    if has_items:
        # Render each item on its own line (like a store receipt)
        shown = 0
        max_rows = 12
        for it in items[:max_rows]:
            name = _safe_txt(it.get("name") or "")
            kind = str(it.get("kind") or "").strip().lower()
            qty = it.get("qty") or 1
            try:
                qty = int(qty)
            except Exception:
                qty = 1
            if qty <= 0:
                qty = 1
            up = it.get("unit_price")
            try:
                up_f = float(up) if up not in (None, "") else None
            except Exception:
                up_f = None
            # Left label
            kind_label = ""
            if kind in ("main","side","other") and kind:
                kind_label = f" ({kind.capitalize()})"
            label = f"{name}{kind_label} ×{qty}"
            # Wrap to max 2 lines per item (to avoid overflow)
            lines = _wrap_text(label, left_max_w, size=11, max_lines=2) or [label]
            # Right label (line total if unit_price is present)
            if up_f is not None:
                line_total = qty * up_f
                line_money = f"{int(round(line_total))} {currency}".strip() if currency else f"{int(round(line_total))}"
            else:
                line_money = ""
            c.drawString(margin, y_desc, lines[0])
            if line_money:
                c.drawRightString(W - margin, y_desc, line_money)
            if len(lines) > 1:
                c.drawString(margin, y_desc - 14, lines[1])
                y_desc -= 14
            y_desc -= 16
            shown += 1
        if len(items) > max_rows:
            c.setFillColorRGB(0.35, 0.38, 0.42)
            c.setFont("Helvetica", 10)
            c.drawString(margin, y_desc, ("…" if lang=="no" else "..."))
            c.setFillColorRGB(0.12, 0.14, 0.18)
            c.setFont("Helvetica", 11)
            y_desc -= 16

        # Total row
        c.setStrokeColorRGB(0.92, 0.93, 0.95)
        c.line(margin, y_desc, W - margin, y_desc)
        y_desc -= 16
        c.setFont("Helvetica-Bold", 13)
        c.drawString(margin, y_desc, L["total"])
        c.drawRightString(W - margin, y_desc, money)
        c.setFont("Helvetica", 11)
        y_after_desc = y_desc
    else:
        # Fallback to the single description line
        desc_text = desc or ("Salg" if lang=="no" else "Sale")
        desc_lines = _wrap_text(desc_text, left_max_w, size=11, max_lines=3) or [desc_text]
        c.drawString(margin, y_desc, desc_lines[0])
        c.drawRightString(W - margin, y_desc, money)
        for i, ln in enumerate(desc_lines[1:], start=1):
            c.drawString(margin, y_desc - 14*i, ln)
        y_after_desc = y_desc - 14*(len(desc_lines)-1)


    if note:
        c.setFillColorRGB(0.35, 0.38, 0.42)
        c.setFont("Helvetica", 10)
        c.drawString(margin, y_after_desc - 16, L["note"] + ": " + note[:120])

    # Total
    total_y = (y_after_desc - 52) if note else (y_after_desc - 36)
    c.setStrokeColorRGB(0.92, 0.93, 0.95)
    c.line(margin, total_y + 8, W - margin, total_y + 8)

    c.setFillColorRGB(0.08, 0.10, 0.12)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin, total_y - 2, L["total"])
    c.drawRightString(W - margin, total_y - 2, money)

    # Footer: share link (optional)
    try:
        # Payment note
        c.setFillColorRGB(0.35, 0.38, 0.42)
        c.setFont("Helvetica", 9)
        c.drawString(margin, 24 * mm, L["generated"])
        base = str(request.base_url).rstrip('/')
        pub = _safe_txt(receipt.get('public_token'))
        if pub:
            link = f"{base}/r/{pub}.pdf"
            c.setFillColorRGB(0.35, 0.38, 0.42)
            c.setFont("Helvetica", 9)
            c.drawString(margin, 18 * mm, link)
    except Exception:
        pass

    c.showPage()
    c.save()
    pdf.seek(0)
    return pdf


@app.post("/api/owner/{token}/receipts")
async def owner_create_receipt(token: str, request: Request, payload: dict):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    try:
        item = create_receipt(int(listing["id"]), payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    base = str(request.base_url).rstrip('/')
    item["share_pdf_url"] = f"{base}/r/{item.get('public_token')}.pdf" if item.get('public_token') else ""
    item["download_pdf_url"] = f"/api/owner/{token}/receipts/{item.get('id')}.pdf"
    return {"ok": True, "item": item}


@app.get("/api/owner/{token}/receipts")
def owner_list_receipts(token: str,
                        date_from: str = "",
                        date_to: str = "",
                        q: str = "",
                        include_replaced: int = 0,
                        limit: int = 200,
                        offset: int = 0):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    df = date_from.strip() or None
    dt = date_to.strip() or None
    qq = q.strip() or None
    items, count = list_receipts(
        listing_id=int(listing["id"]),
        date_from=df,
        date_to=dt,
        q=qq,
        limit=min(max(int(limit or 200), 1), 500),
        offset=max(int(offset or 0), 0),
        include_replaced=bool(int(include_replaced or 0)),
    )
    return {"items": items, "count": count, "currency": listing.get('currency') or ''}


@app.get("/api/owner/{token}/receipts/{receipt_id}.pdf")
def owner_receipt_pdf(token: str, receipt_id: int, request: Request, lang: str = "en"):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    r = get_receipt_by_id(int(listing["id"]), int(receipt_id))
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")

    if (r.get('status') or '') == 'replaced':
        raise HTTPException(status_code=400, detail="Receipt is replaced. Send the newest receipt instead.")

    # Backward compat: older receipts may not have items_json stored
    if not (r.get("items_json") or "").strip() and r.get("transaction_id"):
        tx = get_transaction_by_id(int(listing["id"]), int(r.get("transaction_id")))
        if tx and (tx.get("items_json") or "").strip():
            r["items_json"] = tx.get("items_json") or ""
    pdf = _make_receipt_pdf(listing, r, request, lang=lang)
    fn = f"{listing.get('slug')}-receipt-{r.get('receipt_no')}.pdf"
    return _pdf_stream_response(pdf, fn, download=download)


@app.post("/api/owner/{token}/receipts/{receipt_id}/send-email")
def owner_send_receipt_email(token: str, receipt_id: int, request: Request, payload: dict):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')

    r = get_receipt_by_id(int(listing["id"]), int(receipt_id))
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")

    if (r.get('status') or '') == 'replaced':
        raise HTTPException(status_code=400, detail="Receipt is replaced. Send the newest receipt instead.")

    to_email = str(payload.get("to") or payload.get("email") or r.get("buyer_email") or "").strip()
    if not to_email:
        raise HTTPException(status_code=400, detail="Missing recipient email")

    lang = str(payload.get("lang") or "en").strip() or "en"

    # Build PDF
    pdf_buf = _make_receipt_pdf(listing, r, request, lang=lang)
    pdf_bytes = pdf_buf.getvalue() if hasattr(pdf_buf, "getvalue") else pdf_buf.read()

    listing_name = listing.get("name") or listing.get("title") or listing.get("slug") or "RiceMap24"
    receipt_no = r.get("receipt_no") or f"#{r.get('id')}"
    doc_type = (r.get("doc_type") or "receipt").lower()

    subject = str(payload.get("subject") or f"{doc_type.title()} {receipt_no} — {listing_name}")

    public_url = f"{request.base_url}r/{r.get('public_token')}.pdf"
    body = str(payload.get("message") or "")
    if not body.strip():
        amt = r.get('amount')
        cur = r.get('currency') or (listing.get('currency') or '')
        paid_date = r.get('paid_date') or ''
        pm = r.get('payment_method') or ''
        if str(lang).lower().startswith('no'):
            body = (
                "Hei!\n\n"
                f"Vedlagt ligger {('kvitteringen' if doc_type=='receipt' else 'fakturaen')} ({receipt_no}) fra {listing_name}.\n"
                + (f"Beløp: {amt} {cur}\n" if amt is not None and cur else "")
                + (f"Betalt: {paid_date}\n" if paid_date else "")
                + (f"Betalingsmåte: {pm}\n" if pm else "")
                + f"Du kan også åpne PDF-lenken her: {public_url}\n\n"
                "Takk!\n"
            )
        else:
            body = (
                "Hi!\n\n"
                f"Attached is your {doc_type} ({receipt_no}) from {listing_name}.\n"
                + (f"Amount: {amt} {cur}\n" if amt is not None and cur else "")
                + (f"Paid at: {paid_date}\n" if paid_date else "")
                + (f"Payment method: {pm}\n" if pm else "")
                + f"You can also view the PDF here: {public_url}\n\n"
                "Thank you!\n"
            )


    filename = f"{listing.get('slug')}-{doc_type}-{receipt_no}.pdf".replace(" ", "-")

    try:
        _send_email_with_pdf(to_email, subject, body, pdf_bytes, filename)
        updated = set_receipt_email_status(int(listing["id"]), int(receipt_id), to_email, "sent", "")
        return {"ok": True, "item": updated}
    except Exception as e:
        updated = set_receipt_email_status(int(listing["id"]), int(receipt_id), to_email, "error", str(e))
        raise HTTPException(status_code=400, detail=f"Email failed: {e}")


@app.get("/r/{public_token}.pdf")
def public_receipt_pdf(public_token: str, request: Request, lang: str = "en"):
    r = get_receipt_by_public_token(public_token)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    listing = get_by_id(int(r.get("listing_id")))
    if not listing:
        raise HTTPException(status_code=404, detail="Not found")

    # Backward compat: older receipts may not have items_json stored
    if not (r.get("items_json") or "").strip() and r.get("transaction_id"):
        tx = get_transaction_by_id(int(listing["id"]), int(r.get("transaction_id")))
        if tx and (tx.get("items_json") or "").strip():
            r["items_json"] = tx.get("items_json") or ""
    pdf = _make_receipt_pdf(listing, r, request, lang=lang)
    # inline by default
    fn = f"{listing.get('slug')}-receipt-{r.get('receipt_no')}.pdf"
    return StreamingResponse(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename=\"{fn}\""
    })


# --- Premium: Accounting (mini ledger) ----------------------------------------

@app.get("/api/owner/{token}/transactions")
def owner_list_transactions(token: str,
                            date_from: str = "",
                            date_to: str = "",
                            tx_type: str = "",
                            q: str = "",
                            category: str = "",
                            limit: int = 200,
                            offset: int = 0):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')

    # normalize
    df = date_from.strip() or None
    dt = date_to.strip() or None
    tt = tx_type.strip().lower() or None
    qq = q.strip() or None
    cat = category.strip() or None

    items, count = list_transactions(
        listing_id=int(listing["id"]),
        date_from=df,
        date_to=dt,
        tx_type=tt,
        q=qq,
        category=cat,
        limit=min(max(int(limit or 200), 1), 500),
        offset=max(int(offset or 0), 0),
    )
    # Normalize currency to listing settings for UI (currency is per listing, not per tx)
    cur = listing.get("currency") or ""
    for it in items:
        it["currency"] = cur
    totals = summarize_transactions(items)
    return {"items": items, "count": count, "totals": totals, "currency": cur}


@app.get("/api/owner/{token}/transactions/top-customers")
def owner_top_customers(token: str,
                        date_from: str = "",
                        date_to: str = "",
                        limit: int = 10):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    df = date_from.strip() or None
    dt = date_to.strip() or None
    try:
        items = top_customers(
            listing_id=int(listing["id"]),
            date_from=df,
            date_to=dt,
            limit=min(max(int(limit or 10), 1), 50),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"items": items, "currency": listing.get("currency") or ""}


@app.get("/api/owner/{token}/transactions/top-dishes")
def owner_top_dishes(token: str,
                     date_from: str = "",
                     date_to: str = "",
                     limit: int = 10):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    df = date_from.strip() or None
    dt = date_to.strip() or None
    try:
        items = top_dishes(
            listing_id=int(listing["id"]),
            date_from=df,
            date_to=dt,
            limit=min(max(int(limit or 10), 1), 100),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"items": items, "currency": listing.get("currency") or ""}


@app.post("/api/owner/{token}/transactions")
async def owner_create_transaction(token: str, payload: dict):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')

    tx_type = str(payload.get("type") or "").strip().lower()
    if tx_type not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="type must be income or expense")

    try:
        amount = float(payload.get("amount") or 0)
    except Exception:
        amount = 0
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be > 0")

    tx_date = str(payload.get("date") or "").strip() or datetime.utcnow().strftime("%Y-%m-%d")
    category = str(payload.get("category") or "").strip()
    note = str(payload.get("note") or "").strip()
    customer_id = payload.get("customer_id")
    dish_name = payload.get("dish_name") or payload.get("dish") or ""
    qty = payload.get("qty")
    items = payload.get("items") or payload.get("items_json")

    try:
        item = create_transaction(int(listing["id"]), {
            "date": tx_date,
            "type": tx_type,
            "category": category,
            "amount": amount,
            "customer_id": customer_id,
            "dish_name": dish_name,
            "qty": qty,
            "items": items,
            "note": note,
        }, default_currency=listing.get("currency") or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"ok": True, "item": item}


@app.delete("/api/owner/{token}/transactions/{tx_id}")
def owner_delete_transaction(token: str, tx_id: int):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')
    deleted = delete_transaction(listing_id=int(listing["id"]), tx_id=int(tx_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"ok": True}


@app.get("/api/owner/{token}/transactions.csv")
def owner_transactions_csv(token: str,
                           date_from: str = "",
                           date_to: str = "",
                           tx_type: str = "",
                           q: str = "",
                           category: str = ""):
    listing = _resolve_owner_listing(token)
    _require_plan(listing, 'standard')

    df = date_from.strip() or None
    dt = date_to.strip() or None
    tt = tx_type.strip().lower() or None
    qq = q.strip() or None
    cat = category.strip() or None

    items, _ = list_transactions(
        listing_id=int(listing["id"]),
        date_from=df,
        date_to=dt,
        tx_type=tt,
        q=qq,
        category=cat,
        limit=5000,
        offset=0,
    )

    # Optional: enrich with customer details
    custs = list_customers(int(listing["id"]), q="")
    cust_map = {int(c.get("id")): c for c in custs if c.get("id") is not None}

    cur = listing.get("currency") or ""

    output = BytesIO()
    output.write(b'\xef\xbb\xbf')
    import io
    wrapper = io.TextIOWrapper(output, encoding='utf-8', newline='')
    writer = csv.writer(wrapper)
    writer.writerow(["date", "type", "customer_no", "customer_name", "dish", "qty", "category", "amount", "currency", "note"])
    for it in items:
        cid = it.get("customer_id")
        c = cust_map.get(int(cid)) if cid is not None else None
        writer.writerow([
            it.get("date") or "",
            it.get("type") or "",
            (c.get("customer_no") if c else "") or "",
            (c.get("name") if c else "") or "",
            it.get("dish_name") or "",
            it.get("qty") or "",
            it.get("category") or "",
            it.get("amount") or "",
            cur,
            it.get("note") or "",
        ])
    wrapper.flush()
    data = output.getvalue()

    headers = {
        "Content-Disposition": f"attachment; filename=transactions-{listing.get('slug')}.csv",
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(content=data, media_type="text/csv; charset=utf-8", headers=headers)


# --- Preview (shareable draft link) ---
@app.get("/api/preview/{token}")
def get_preview(token: str):
    # Token is normally preview_token. For demo convenience, also accept a slug
    # for published listings (lets you type /p/:slug and still see the preview page).
    item = get_by_preview_token(token)
    if not item:
        item = get_by_slug(token)
        if item and int(item.get("published", 0)) != 1:
            item = None
    if not item:
        raise HTTPException(status_code=404, detail="Preview not found")
    # preview is allowed for drafts + live
    item["_preview"] = True
    return item




def _best_listing_location_query(item: dict) -> str:
    parts = []
    postcode = str((item or {}).get("postcode") or "").strip()
    city = str((item or {}).get("city") or "").strip()
    area = str((item or {}).get("area") or "").strip()
    country = str((item or {}).get("country") or "").strip()
    for x in (postcode, city, area, country):
        if x and x not in parts:
            parts.append(x)
    return ", ".join(parts)


def _geocode_listing_if_missing(listing_id: int, item: Optional[dict] = None) -> None:
    """Best-effort geocode for new/activated kitchens.

    Public map/nearest search require lat/lng. If Nominatim is unavailable,
    signup must still succeed; admin can retry later by editing/re-saving.
    """
    try:
        item = item or get_by_id(int(listing_id)) or {}
        if item.get("lat") is not None and item.get("lng") is not None:
            return
        q = _best_listing_location_query(item)
        if not q:
            return
        res = geocode(q, country=str(item.get("country") or "").strip() or None)
        if res and res.get("ok") and res.get("lat") is not None and res.get("lng") is not None:
            set_listing_coordinates(int(listing_id), float(res["lat"]), float(res["lng"]))
    except Exception:
        pass

# --- Draft / activation ---
@app.post("/api/drafts")
def create_listing_draft(payload: dict):
    """Create a new draft. Returns draft id + preview token."""
    settings = get_admin_settings()
    if not settings.get("public_signups_enabled", True):
        raise HTTPException(status_code=403, detail="Public signups are currently closed")
    try:
        _id, slug, token = create_draft(payload)
        try:
            item = get_by_id(int(_id))
            _geocode_listing_if_missing(int(_id), item)
            item = get_by_id(int(_id)) or item
            email = str(((payload or {}).get("contact") or {}).get("email") or "").strip().lower()
            password = str((payload or {}).get("owner_password") or "")
            display_name = str((payload or {}).get("owner_name") or (payload or {}).get("name") or "Kitchen owner").strip()
            if email and password:
                existing_user = get_app_user_by_email(email)
                if not existing_user:
                    create_app_user(email, password, display_name=display_name, role="owner", listing_id=int(_id), active=True, email_verified=False)
                elif existing_user.get("role") == "owner":
                    # Older staging/test records may have been created before owner accounts were linked.
                    try:
                        conn = connect()
                        try:
                            conn.execute("UPDATE app_users SET listing_id=?, updated_at=datetime('now') WHERE id=? AND (listing_id IS NULL OR listing_id=0)", (int(_id), int(existing_user.get("id") or 0)))
                            conn.commit()
                        finally:
                            conn.close()
                    except Exception:
                        pass
            if item:
                _queue_owner_template_once(item, "welcome_new_owner", "welcome_new_owner")
        except Exception:
            pass
        return {"id": _id, "slug": slug, "preview_token": token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/drafts/{listing_id}")
def update_listing_draft(listing_id: int, payload: dict):
    try:
        update_draft(listing_id, payload)
        return {"ok": True}
    except KeyError:
        raise HTTPException(status_code=404, detail="Draft not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/drafts/{listing_id}")
def get_draft(listing_id: int):
    item = get_by_id(listing_id)
    if not item or int(item.get("published", 0)) == 1:
        # avoid leaking live via draft endpoint; drafts only
        raise HTTPException(status_code=404, detail="Draft not found")
    return item




# --- Billing (Stripe subscriptions) ---

@app.post('/api/billing/create-checkout-session')
async def billing_create_checkout_session(payload: dict, request: Request):
    """Create a Stripe Checkout Session (subscription) for a listing draft.

    Body: {listing_id:int, plan, billing, country}. Currency is derived from country
    server-side to prevent mismatched checkout setups.
    Returns: {url, session_id, plan, billing, country, currency}
    """
    if STRIPE_MODE == 'disabled' and is_production():
        raise HTTPException(status_code=503, detail='Stripe Checkout is disabled in this environment')

    pld = payload or {}
    listing_id = int(pld.get('listing_id') or 0)
    if not listing_id:
        raise HTTPException(status_code=400, detail='listing_id required')

    item = get_by_id(listing_id)
    if not item:
        raise HTTPException(status_code=404, detail='Draft not found')

    checkout = _normalize_checkout_payload(pld, item)
    plan = checkout['plan']
    billing = checkout['billing']
    country = checkout['country']
    currency = checkout['currency']
    discount_code = checkout['discount_code']
    referred_by_code = checkout['referred_by_code']
    referral_credit_to_apply = checkout['referral_credit_to_apply']

    # Mark as pending activation after server-side validation.
    # In staging/local without Stripe keys, allow a safe test path so signup,
    # draft creation and PostgreSQL persistence can be tested before Stripe is configured.
    token = request_activation(listing_id, plan=plan, billing=billing)

    origin = _origin_from_request(request)

    if not STRIPE_SECRET_KEY:
        if is_production():
            raise HTTPException(status_code=503, detail='Stripe Checkout is not configured yet (missing STRIPE_SECRET_KEY)')
        try:
            admin_update_meta(
                listing_id,
                plan=plan,
                billing=billing,
                plan_active=1,
                paid_status='paid',
                account_status='active',
                access_type='internal',
                access_reason='Staging/local checkout bypass because Stripe is not configured yet.',
            )
            slug = admin_activate(listing_id)
            _geocode_listing_if_missing(listing_id, get_by_id(listing_id))
        except Exception:
            slug = item.get('slug') or ''
        return {
            'ok': True,
            'staging_bypass': True,
            'url': f'{origin}/p/{token}',
            'listing_id': listing_id,
            'slug': slug,
            'plan': plan,
            'billing': billing,
            'country': country,
            'currency': currency,
            'message': 'Stripe is not configured. Staging/local bypass created and activated the test kitchen.',
        }

    price_id = _stripe_price_id(plan, billing, country=country, currency=currency)

    email = ((item.get('contact') or {}).get('email') or '').strip()
    metadata = {
        'listing_id': str(listing_id),
        'slug': item.get('slug') or '',
        'plan': plan,
        'billing': billing,
        'country': country,
        'currency': currency,
        'preview_token': token or (item.get('preview_token') or ''),
        'discount_code': discount_code,
        'referred_by_code': referred_by_code,
        'referral_credit_to_apply': referral_credit_to_apply,
    }

    session = stripe.checkout.Session.create(
        mode='subscription',
        line_items=[{'price': price_id, 'quantity': 1}],
        success_url=f"{origin}/pay/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{origin}/pay/cancel",
        customer_email=(email if email else None),
        client_reference_id=str(listing_id),
        metadata=metadata,
        subscription_data={'metadata': metadata},
        billing_address_collection='required',
        tax_id_collection={'enabled': True},
        allow_promotion_codes=True,
    )

    try:
        stripe_mark_checkout_session(listing_id, session.id, price_id=price_id, status='checkout_created')
    except Exception:
        pass

    return {
        'ok': True,
        'url': session.url,
        'session_id': session.id,
        'plan': plan,
        'billing': billing,
        'country': country,
        'currency': currency,
    }


@app.get('/api/billing/confirm')
async def billing_confirm(session_id: str):
    """Fallback confirmation for local dev (when webhooks aren't configured).

    The frontend hits this on /pay/success. It verifies the session via Stripe API
    and activates/deactivates accordingly.
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail='Stripe not configured')
    if not session_id:
        raise HTTPException(status_code=400, detail='session_id required')

    session = stripe.checkout.Session.retrieve(session_id, expand=['subscription'])
    md = (session.get('metadata') or {})
    listing_id = int(md.get('listing_id') or 0)
    if not listing_id:
        raise HTTPException(status_code=400, detail='Missing listing_id in session metadata')

    status = session.get('status')
    pay = session.get('payment_status')
    if status not in ('complete', 'completed') and pay != 'paid':
        return {'ok': False, 'status': status, 'payment_status': pay}

    sub = session.get('subscription')
    sub_id = sub.get('id') if isinstance(sub, dict) else sub
    sub_status = (sub.get('status') if isinstance(sub, dict) else None) or 'active'

    cpe = None
    if isinstance(sub, dict) and sub.get('current_period_end'):
        import datetime
        cpe = datetime.datetime.utcfromtimestamp(int(sub['current_period_end'])).strftime('%Y-%m-%d')

    stripe_mark_subscription_active(
        listing_id=listing_id,
        customer_id=str(session.get('customer') or ''),
        subscription_id=str(sub_id or ''),
        status=str(sub_status or ''),
        current_period_end=cpe,
    )

    return {'ok': True, 'listing_id': listing_id, 'slug': md.get('slug') or '', 'preview_token': md.get('preview_token') or ''}


@app.post('/api/billing/webhook')
async def billing_webhook(request: Request):
    """Stripe webhook endpoint.

    Set STRIPE_WEBHOOK_SECRET and configure Stripe to send events here.
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail='Stripe webhook secret not configured')

    body = await request.body()
    sig = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(body, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Invalid signature: {e}')

    etype = event.get('type')
    obj = (event.get('data') or {}).get('object') or {}
    event_id = str(event.get('id') or '')
    if _stripe_event_already_seen(event_id):
        return {'ok': True, 'duplicate': True}
    sub_for_log = str(obj.get('subscription') or obj.get('id') or '')
    customer_for_log = str(obj.get('customer') or '')
    listing_for_log = None
    try:
        md_for_log = obj.get('metadata') or {}
        listing_for_log = int(md_for_log.get('listing_id') or 0) or None
    except Exception:
        listing_for_log = None

    processed_message = 'Received webhook event.'
    processed_status = 'ignored'

    try:
        if etype == 'checkout.session.completed':
            md = obj.get('metadata') or {}
            listing_id = int(md.get('listing_id') or 0)
            if listing_id:
                listing_for_log = listing_id
                processed_status = 'processed'
                processed_message = 'Checkout completed; subscription marked active.'
                stripe_mark_subscription_active(
                    listing_id=listing_id,
                    customer_id=str(obj.get('customer') or ''),
                    subscription_id=str(obj.get('subscription') or ''),
                    status='active',
                    current_period_end=_stripe_subscription_period_end(obj),
                )

        elif etype == 'invoice.paid':
            sub_id = obj.get('subscription')
            if sub_id:
                listing = get_by_stripe_subscription_id(str(sub_id))
                if listing:
                    listing_for_log = int(listing.get('id'))
                    processed_status = 'processed'
                    processed_message = 'Invoice paid; subscription marked active.'
                    stripe_mark_subscription_active(
                        listing_id=int(listing.get('id')),
                        customer_id=str(listing.get('stripe_customer_id') or ''),
                        subscription_id=str(sub_id),
                        status='active',
                        current_period_end=_stripe_subscription_period_end(obj) or _stripe_ts_to_date(obj.get('period_end')),
                    )

        elif etype in ('customer.subscription.deleted', 'customer.subscription.updated'):
            sub_id = obj.get('id')
            st = (obj.get('status') or '').lower()
            if sub_id and st and st not in ('active', 'trialing'):
                listing = get_by_stripe_subscription_id(str(sub_id))
                if listing:
                    listing_for_log = int(listing.get('id'))
                processed_status = 'processed'
                processed_message = f'Subscription marked inactive: {st}'
                stripe_mark_inactive_by_subscription(str(sub_id), status=st)
            elif sub_id and st in ('active', 'trialing'):
                listing = get_by_stripe_subscription_id(str(sub_id))
                if listing:
                    listing_for_log = int(listing.get('id'))
                    processed_status = 'processed'
                    processed_message = f'Subscription updated: {st}'
                    cpe = None
                    cpe_ts = obj.get('current_period_end')
                    if cpe_ts:
                        import datetime
                        cpe = datetime.datetime.utcfromtimestamp(int(cpe_ts)).strftime('%Y-%m-%d')
                    stripe_mark_subscription_active(
                        listing_id=int(listing.get('id')),
                        customer_id=str(obj.get('customer') or listing.get('stripe_customer_id') or ''),
                        subscription_id=str(sub_id),
                        status=st,
                        current_period_end=cpe,
                    )

    except Exception as e:
        # Do not fail webhook delivery on bookkeeping errors. Log the event so admin can see it.
        processed_status = 'error'
        processed_message = f'Webhook bookkeeping error: {e}'

    try:
        record_stripe_webhook_event(
            str(etype or 'unknown'),
            event_id=event_id,
            listing_id=listing_for_log,
            subscription_id=sub_for_log,
            customer_id=customer_for_log,
            status=processed_status,
            source='webhook',
            message=processed_message,
            details={'object_id': obj.get('id'), 'livemode': event.get('livemode')},
            payload={'type': etype, 'object': {'id': obj.get('id'), 'object': obj.get('object'), 'status': obj.get('status')}},
        )
    except Exception:
        pass

    return {'ok': True}


@app.post("/api/drafts/{listing_id}/request-activation")
def request_listing_activation(listing_id: int, payload: dict):
    """User requests to go live. Admin will activate after manual payment."""
    try:
        plan = (payload or {}).get("plan", "basic")
        billing = (payload or {}).get("billing", "monthly")
        token = request_activation(listing_id, plan=plan, billing=billing)
        item = get_by_id(listing_id) or {}
        return {
            "ok": True,
            "pending": bool(int(item.get("pending_activation", 0) or 0)),
            "published": bool(int(item.get("published", 0) or 0)),
            "preview_token": token,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Draft not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# --- Auth/session foundation -------------------------------------------------
@app.post("/api/auth/dev-create-admin")
async def auth_dev_create_admin(payload: dict, request: Request, key: Optional[str] = None):
    """Local/staging helper for creating the first admin user.

    In production this endpoint is disabled. Development may create the
    first local admin directly. Staging/public environments require an
    existing admin session or explicitly enabled legacy key fallback.
    """
    if is_production():
        raise HTTPException(status_code=404, detail="Not found")
    existing_admins = [u for u in list_app_users() if u.get("role") == "admin"]
    # Local development may create the first admin directly. Staging/public
    # environments must use an existing admin session or explicitly enabled
    # legacy key fallback.
    if runtime_config.env != "development" and not _admin_authorized(request=request, key=key):
        raise HTTPException(status_code=401, detail="Admin bootstrap requires authorization outside development")
    if existing_admins and not _admin_authorized(request=request, key=key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    p = payload or {}
    email = str(p.get("email") or "").strip().lower()
    password = str(p.get("password") or "")
    display_name = str(p.get("display_name") or "Admin").strip() or "Admin"
    if get_app_user_by_email(email):
        raise HTTPException(status_code=409, detail="User already exists")
    try:
        user = create_app_user(email, password, display_name=display_name, role="admin", active=True, email_verified=True)
        log_admin_activity("auth_admin_created", entity_type="app_user", entity_id=int(user.get("id") or 0), title="Created local admin user", details={"email": email})
        return {"ok": True, "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _auth_user_response(user: Optional[dict]) -> dict:
    data = {"ok": True, "authenticated": bool(user), "user": user}
    if user and str(user.get("role") or "") == "owner" and user.get("listing_id"):
        try:
            listing = get_by_id(int(user.get("listing_id") or 0))
            if listing:
                data["owner_dashboard"] = {
                    "listing_id": int(listing.get("id") or user.get("listing_id") or 0),
                    "slug": listing.get("slug") or "",
                    "preview_token": listing.get("preview_token") or "",
                    "name": listing.get("name") or "",
                    "path": "/p/" + str(listing.get("preview_token") or ""),
                }
        except Exception:
            pass
    return data


@app.post("/api/auth/login")
async def auth_login(payload: dict, request: Request):
    p = payload or {}
    email = str(p.get("email") or "").strip().lower()
    password = str(p.get("password") or "")
    ip = _request_ip(request)
    failed = recent_failed_login_count(email, ip, minutes=runtime_config.login_lockout_minutes)
    if failed >= runtime_config.login_max_failed_attempts:
        record_login_attempt(email, ip, success=False, reason="rate_limited")
        raise HTTPException(status_code=429, detail="Too many failed login attempts. Try again later.")
    user = authenticate_app_user(email, password)
    if not user:
        # Staging compatibility: migrate older owner records that were created
        # before app_users/session auth was fully linked. This is only used after
        # normal authentication fails and requires an exact email + password match
        # against the original listing payload.
        user = authenticate_or_migrate_legacy_owner(email, password)
    if not user:
        record_login_attempt(email, ip, success=False, reason="invalid_credentials")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    cleanup_expired_app_sessions()
    record_login_attempt(email, ip, success=True, reason="login")
    token, session = create_app_session(
        int(user["id"]),
        role=str(user.get("role") or "owner"),
        ip=ip,
        user_agent=request.headers.get("user-agent", ""),
        days=runtime_config.session_days,
    )
    payload_out = _auth_user_response(user)
    payload_out["expires_at"] = session.get("expires_at")
    response = JSONResponse(payload_out)
    response.set_cookie(SESSION_COOKIE_NAME, token, **_session_cookie_kwargs())
    return response




@app.post("/api/auth/dev-reset-admin")
async def auth_dev_reset_admin(payload: dict, request: Request):
    """Non-production recovery: reset the local/staging admin login.

    This is for staging databases where an old admin password no longer works.
    It replaces only app_users with role=admin and admin sessions. It does not
    delete listings, owner users, kitchen pages, images, tickets or settings.
    """
    # Recovery is for non-live staging/local databases. On Render, some staging
    # services can accidentally have RICEMAP_ENV=production, so allow this only
    # when the service/public URL clearly says staging.
    service_hint = (os.environ.get("RENDER_SERVICE_NAME", "") + " " + os.environ.get("RENDER_EXTERNAL_URL", "")).lower()
    if is_production() and "staging" not in service_hint:
        raise HTTPException(status_code=404, detail="Not found")
    p = payload or {}
    if str(p.get("confirm") or "").strip().upper() != "RESET":
        raise HTTPException(status_code=400, detail="Type RESET to confirm")
    email = str(p.get("email") or "").strip().lower()
    password = str(p.get("password") or "")
    display_name = str(p.get("display_name") or "Admin").strip() or "Admin"
    try:
        user = reset_admin_app_users(email, password, display_name=display_name)
        log_admin_activity("auth_admin_reset", actor="system", entity_type="app_user", entity_id=int(user.get("id") or 0), title="Reset local/staging admin login", details={"email": email})
        return {"ok": True, "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/auth/logout")
async def auth_logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME) or ""
    if token:
        revoke_app_session(token)
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


@app.get("/api/auth/me")
async def auth_me(request: Request):
    user = _current_user_from_request(request)
    return _auth_user_response(user)


@app.get("/api/auth/bootstrap-status")
async def auth_bootstrap_status(request: Request, key: Optional[str] = None):
    """Expose only safe bootstrap information for the admin login screen.

    This keeps first-admin creation explicit in local/staging, while making it
    clear when the normal action is login rather than creating another admin.
    """
    admins = [u for u in list_app_users() if u.get("role") == "admin"]
    has_admin = bool(admins)
    legacy_authorized = _admin_authorized(request=request, key=key)
    can_create_first_admin = (runtime_config.env == "development") and (not has_admin)
    can_create_with_legacy = runtime_config.legacy_admin_key_available and legacy_authorized
    return {
        "ok": True,
        "environment": runtime_config.env,
        "production": is_production(),
        "has_admin": has_admin,
        "admin_count": len(admins),
        "can_create_first_admin": can_create_first_admin,
        "can_create_with_legacy": can_create_with_legacy,
        "legacy_key_fallback_available": bool(runtime_config.legacy_admin_key_available),
    }


@app.get("/api/admin/auth/users")
async def admin_auth_users(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return {"items": list_app_users()}

# --- Admin (manual activation) ---
def _check_admin(key: Optional[str], request: Optional[Request] = None) -> None:
    if not _admin_authorized(request=request, key=key):
        raise HTTPException(status_code=401, detail="Unauthorized")

def _require_admin(key: Optional[str] = None, request: Optional[Request] = None) -> None:
    _check_admin(key, request=request)


@app.get("/api/admin/listings")
def admin_listings(request: Request, key: Optional[str] = None, status: str = "pending"):
    _check_admin(key, request=request)
    items = admin_list(status=status)
    # Return smaller payload to keep UI snappy
    out = []
    for i in items:
        c = (i.get("contact") or {})
        out.append(
            {
                "id": i.get("id"),
                "slug": i.get("slug"),
                "name": i.get("name"),
                "area": i.get("area"),
                "city": i.get("city"),
                "postcode": i.get("postcode"),
                "country": i.get("country"),
                "plan": i.get("plan"),
                "billing": i.get("billing"),
                "published": i.get("published"),
                "plan_active": i.get("plan_active"),
                "account_status": i.get("account_status", "active"),
                "deletion_requested_at": i.get("deletion_requested_at", ""),
                "deletion_scheduled_for": i.get("deletion_scheduled_for", ""),
                "deletion_restore_available": i.get("deletion_restore_available", False),
                "pending_activation": i.get("pending_activation"),
                "preview_token": i.get("preview_token"),
                "requested_at": i.get("requested_at"),
                "activated_at": i.get("activated_at"),
                "admin_note": i.get("admin_note", ""),
                "paid_status": i.get("paid_status", "unpaid"),
                "paid_until": i.get("paid_until"),
                "last_payment_at": i.get("last_payment_at"),
                "billing_visibility": i.get("billing_visibility", "hidden"),
                "billing_access_valid": i.get("billing_access_valid", False),
                "billing_access_source": i.get("billing_access_source", "none"),
                "access_type": i.get("access_type", "paid"),
                "access_expires_at": i.get("access_expires_at", ""),
                "access_reason": i.get("access_reason", ""),
                "feature_overrides": i.get("feature_overrides", []),
                "stripe_status": i.get("stripe_status"),
                "stripe_subscription_id": i.get("stripe_subscription_id"),
                "stripe_customer_id": i.get("stripe_customer_id"),
                "stripe_current_period_end": i.get("stripe_current_period_end"),
                "referral_code": i.get("referral_code"),
                "referred_by_code": i.get("referred_by_code"),
                "referral_credit_balance": i.get("referral_credit_balance", 0),
                "referral_credit_total_earned": i.get("referral_credit_total_earned", 0),
                "successful_referrals": i.get("successful_referrals", 0),
                "pending_referrals": i.get("pending_referrals", 0),
                "hero_image": i.get("hero_image"),
                "signature_image": i.get("signature_image"),
                "menu_count": len(i.get("menu") or []),
                "lat": i.get("lat"),
                "lng": i.get("lng"),
                "has_contact": bool((c.get("phone") or "").strip() or (c.get("email") or "").strip() or (c.get("whatsapp") or "").strip() or (c.get("instagram") or "").strip()),
                "has_location": bool((i.get("city") or "").strip() or str(i.get("postcode") or "").strip()),
                "contact_phone": c.get("phone") or "",
                "contact_email": c.get("email") or "",
                "contact_whatsapp": c.get("whatsapp") or "",
            }
        )
    return {"items": out, "count": len(out)}




@app.get("/api/admin/production-readiness")
def admin_production_readiness(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return _production_readiness_snapshot()


@app.get("/api/admin/pilot-readiness")
def admin_pilot_readiness(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return _pilot_readiness_snapshot()


@app.get("/api/admin/prelaunch-readiness")
def admin_prelaunch_readiness(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return _prelaunch_readiness_snapshot()


@app.post("/api/admin/production-review")
def admin_production_review(payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    snapshot = _production_readiness_snapshot()
    note = str((payload or {}).get("note") or "").strip()
    missing = (payload or {}).get("missing")
    if not isinstance(missing, list):
        missing = [c.get("id") or c.get("label") for c in snapshot.get("checks", []) if not c.get("ready")]
    details = {
        "ready_count": snapshot.get("ready_count", 0),
        "total_count": snapshot.get("total_count", 0),
        "mode": snapshot.get("mode", "local-mvp"),
        "missing": missing,
        "stripe_event_count": int((payload or {}).get("stripe_event_count") or 0),
        "stripe_error_count": int((payload or {}).get("stripe_error_count") or 0),
    }
    if note:
        details["note"] = note[:500]
    title = f"Production review: {details['ready_count']}/{details['total_count']} checks ready"
    log_admin_activity("production_review", actor="admin", entity_type="production", title=title, details=details)
    return {"ok": True, "details": details}


@app.get("/api/admin/settings")
def admin_get_settings(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    settings = get_admin_settings()
    settings.update(_email_secret_status(settings))
    settings["email_effective_config"] = _email_config_snapshot(settings)
    return {"settings": settings}


@app.post("/api/admin/settings")
def admin_update_settings(payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    settings = update_admin_settings(payload or {})
    try:
        log_admin_activity("settings_update", entity_type="admin_settings", title="Updated admin settings", details={"patch": payload or {}})
    except Exception:
        pass
    settings.update(_email_secret_status(settings))
    return {"ok": True, "settings": settings}


@app.get("/api/admin/email/config")
def admin_email_config(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return _email_config_snapshot(get_admin_settings())


@app.get("/api/admin/deployment/config")
def admin_deployment_config(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return _deployment_config_snapshot()


@app.get("/api/admin/backup/config")
def admin_backup_config(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return _backup_config_snapshot()


@app.get("/api/admin/monitoring/config")
def admin_monitoring_config(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return _monitoring_config_snapshot()


@app.get("/api/admin/error-logs")
def admin_error_logs(request: Request, key: Optional[str] = None, limit: int = 100, level: str = "all", q: str = ""):
    _check_admin(key, request=request)
    return {"items": list_app_error_logs(limit=limit, level=level, q=q)}


@app.post("/api/admin/error-logs/cleanup")
def admin_error_logs_cleanup(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    deleted = cleanup_app_error_logs(runtime_config.error_log_retention_days)
    try:
        log_admin_activity("error_log_cleanup", entity_type="monitoring", title="Cleaned up old app error logs", details={"deleted": deleted, "retention_days": runtime_config.error_log_retention_days})
    except Exception:
        pass
    return {"ok": True, "deleted": deleted, "retention_days": runtime_config.error_log_retention_days}


@app.post("/api/admin/backup/local-run")
def admin_backup_local_run(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    result = _run_local_backup()
    try:
        log_admin_activity("backup_run", actor="admin", entity_type="backup", title="Created local backup", details=result)
    except Exception:
        pass
    return result



def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default

def _env_bool(*names: str, default: Optional[bool] = None) -> Optional[bool]:
    for name in names:
        value = os.environ.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}
    return default

def _email_settings_with_env(settings: Optional[dict] = None) -> dict:
    """Merge DB admin email settings with deployment env overrides.

    This lets staging/production be configured from Render env vars without
    relying on a manual admin-settings click after each new database. Secrets
    are still never returned to the UI.
    """
    merged = dict(settings or get_admin_settings())
    mappings = {
        "email_provider": ("RICEMAP24_EMAIL_PROVIDER",),
        "email_from_name": ("RICEMAP24_EMAIL_FROM_NAME",),
        "email_from_email": ("RICEMAP24_EMAIL_FROM", "RICEMAP24_EMAIL_FROM_EMAIL", "RICEMAP_SMTP_FROM"),
        "email_reply_to": ("RICEMAP24_EMAIL_REPLY_TO",),
        "admin_notification_email": ("RICEMAP24_ADMIN_NOTIFICATION_EMAIL",),
        "smtp_host": ("RICEMAP24_SMTP_HOST", "SMTP_HOST", "RICEMAP_SMTP_HOST"),
        "smtp_username": ("RICEMAP24_SMTP_USERNAME", "SMTP_USERNAME", "RICEMAP_SMTP_USER"),
        "smtp_port": ("RICEMAP24_SMTP_PORT", "SMTP_PORT", "RICEMAP_SMTP_PORT"),
    }
    for key, names in mappings.items():
        value = _first_env(*names)
        if value:
            merged[key] = value
    for key, names in {
        "email_delivery_enabled": ("RICEMAP24_EMAIL_DELIVERY_ENABLED",),
        "email_dns_verified": ("RICEMAP24_EMAIL_DNS_VERIFIED",),
    }.items():
        value = _env_bool(*names, default=None)
        if value is not None:
            merged[key] = value
    return merged

def _email_secret_status(settings: Optional[dict] = None) -> dict:
    """Return secret availability without exposing secret values."""
    return {
        "smtp_password_set": bool(os.environ.get("RICEMAP24_SMTP_PASSWORD") or os.environ.get("SMTP_PASSWORD") or os.environ.get("RICEMAP_SMTP_PASS")),
        "sendgrid_api_key_set": bool(os.environ.get("RICEMAP24_SENDGRID_API_KEY") or os.environ.get("SENDGRID_API_KEY")),
        "postmark_server_token_set": bool(os.environ.get("RICEMAP24_POSTMARK_SERVER_TOKEN") or os.environ.get("POSTMARK_SERVER_TOKEN")),
    }


def _email_config_snapshot(settings: Optional[dict] = None) -> dict:
    """Admin/health safe email configuration snapshot. Never returns secret values."""
    settings = _email_settings_with_env(settings)
    provider = str(settings.get("email_provider") or "manual").strip().lower()
    if provider not in {"manual", "smtp", "sendgrid", "postmark"}:
        provider = "manual"
    secret_status = _email_secret_status(settings)
    provider_secret_ready = True
    provider_config_ready = True
    missing: list[str] = []
    if provider == "smtp":
        provider_config_ready = bool(str(settings.get("smtp_host") or "").strip() and str(settings.get("smtp_username") or "").strip())
        provider_secret_ready = bool(secret_status.get("smtp_password_set"))
        if not str(settings.get("smtp_host") or "").strip():
            missing.append("smtp_host")
        if not str(settings.get("smtp_username") or "").strip():
            missing.append("smtp_username")
        if not provider_secret_ready:
            missing.append("RICEMAP24_SMTP_PASSWORD")
    elif provider == "sendgrid":
        provider_secret_ready = bool(secret_status.get("sendgrid_api_key_set"))
        if not provider_secret_ready:
            missing.append("RICEMAP24_SENDGRID_API_KEY")
    elif provider == "postmark":
        provider_secret_ready = bool(secret_status.get("postmark_server_token_set"))
        if not provider_secret_ready:
            missing.append("RICEMAP24_POSTMARK_SERVER_TOKEN")
    delivery_enabled = bool(settings.get("email_delivery_enabled"))
    from_email = str(settings.get("email_from_email") or "").strip()
    reply_to = str(settings.get("email_reply_to") or "").strip()
    admin_to = str(settings.get("admin_notification_email") or "").strip()
    if not from_email or "@" not in from_email:
        missing.append("email_from_email")
    if not admin_to or "@" not in admin_to:
        missing.append("admin_notification_email")
    dns_ready = bool(settings.get("email_dns_verified") or False)
    ready_for_real_delivery = bool(
        delivery_enabled
        and provider in {"smtp", "sendgrid", "postmark"}
        and provider_config_ready
        and provider_secret_ready
        and from_email
        and admin_to
    )
    return {
        "provider": provider,
        "delivery_enabled": delivery_enabled,
        "provider_config_ready": provider_config_ready,
        "provider_secret_ready": provider_secret_ready,
        "ready_for_real_delivery": ready_for_real_delivery,
        "dns_verified": dns_ready,
        "from_name": str(settings.get("email_from_name") or "RiceMap24"),
        "from_email": from_email,
        "reply_to": reply_to,
        "admin_notification_email": admin_to,
        "missing": sorted(set(missing)),
        "secret_status": secret_status,
        "safe_mode": (not delivery_enabled) or provider == "manual",
    }


def _send_transactional_email(to_email: str, subject: str, body: str, *, attachments: Optional[list[dict]] = None, settings: Optional[dict] = None) -> dict:
    """Send one transactional email through the configured provider.

    Used for receipt emails and can be reused for other critical system emails.
    Returns safe delivery metadata and never exposes provider secrets.
    """
    settings = _email_settings_with_env(settings)
    cfg = _email_config_snapshot(settings)
    provider = str(cfg.get("provider") or "manual").lower()
    if not cfg.get("delivery_enabled") or provider == "manual":
        raise RuntimeError("Email delivery is disabled or set to manual mode")
    if not cfg.get("provider_config_ready") or not cfg.get("provider_secret_ready"):
        missing = ", ".join(cfg.get("missing") or [])
        raise RuntimeError(f"Email provider is not fully configured{': ' + missing if missing else ''}")

    to_email = (to_email or "").strip()
    if not to_email or "@" not in to_email:
        raise RuntimeError("Missing or invalid recipient email")
    subject = (subject or "RiceMap24 notification")[:240]
    body = body or " "
    attachments = attachments or []
    from_name = str(cfg.get("from_name") or "RiceMap24").strip()
    from_email = str(cfg.get("from_email") or "").strip()
    reply_to = str(cfg.get("reply_to") or from_email).strip()
    if not from_email or "@" not in from_email:
        raise RuntimeError("Missing or invalid from email")

    if provider == "smtp":
        password = os.environ.get("RICEMAP24_SMTP_PASSWORD") or os.environ.get("SMTP_PASSWORD") or os.environ.get("RICEMAP_SMTP_PASS")
        host = str(settings.get("smtp_host") or "").strip()
        port = int(settings.get("smtp_port") or 587)
        username = str(settings.get("smtp_username") or from_email).strip()
        if not host or not password:
            raise RuntimeError("SMTP host/password secret missing")
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
        msg["To"] = to_email
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.set_content(body)
        for att in attachments:
            content = att.get("content") or b""
            msg.add_attachment(
                content,
                maintype=att.get("maintype") or "application",
                subtype=att.get("subtype") or "octet-stream",
                filename=att.get("filename") or "attachment.bin",
            )
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as smtp:
                if username:
                    smtp.login(username, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                if username:
                    smtp.login(username, password)
                smtp.send_message(msg)
        return {"ok": True, "provider": "smtp"}

    if provider == "postmark":
        token = os.environ.get("RICEMAP24_POSTMARK_SERVER_TOKEN") or os.environ.get("POSTMARK_SERVER_TOKEN")
        if not token:
            raise RuntimeError("Postmark server token secret missing")
        payload = {
            "From": f"{from_name} <{from_email}>" if from_name else from_email,
            "To": to_email,
            "Subject": subject,
            "TextBody": body,
            "ReplyTo": reply_to or from_email,
        }
        # Postmark attachments are base64 encoded.
        if attachments:
            import base64
            payload["Attachments"] = []
            for att in attachments:
                payload["Attachments"].append({
                    "Name": att.get("filename") or "attachment.bin",
                    "Content": base64.b64encode(att.get("content") or b"").decode("ascii"),
                    "ContentType": f"{att.get('maintype') or 'application'}/{att.get('subtype') or 'octet-stream'}",
                })
        r = httpx.post(
            "https://api.postmarkapp.com/email",
            headers={"X-Postmark-Server-Token": token, "Content-Type": "application/json", "Accept": "application/json"},
            json=payload,
            timeout=20,
        )
        if r.status_code >= 300:
            raise RuntimeError(f"Postmark error {r.status_code}: {r.text[:300]}")
        return {"ok": True, "provider": "postmark"}

    if provider == "sendgrid":
        api_key = os.environ.get("RICEMAP24_SENDGRID_API_KEY") or os.environ.get("SENDGRID_API_KEY")
        if not api_key:
            raise RuntimeError("SendGrid API key secret missing")
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_email, "name": from_name or "RiceMap24"},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }
        if reply_to:
            payload["reply_to"] = {"email": reply_to}
        if attachments:
            import base64
            payload["attachments"] = []
            for att in attachments:
                payload["attachments"].append({
                    "filename": att.get("filename") or "attachment.bin",
                    "type": f"{att.get('maintype') or 'application'}/{att.get('subtype') or 'octet-stream'}",
                    "disposition": "attachment",
                    "content": base64.b64encode(att.get("content") or b"").decode("ascii"),
                })
        r = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=20,
        )
        if r.status_code >= 300:
            raise RuntimeError(f"SendGrid error {r.status_code}: {r.text[:300]}")
        return {"ok": True, "provider": "sendgrid"}

    raise RuntimeError(f"Unknown email provider: {provider}")


def _send_admin_notification_item(item: dict, settings: Optional[dict] = None) -> dict:
    """Send one queued admin notification through the configured provider.

    Manual mode is intentionally a safe MVP simulation. SMTP/SendGrid/Postmark only
    attempt real delivery when the needed server-side secret is present.
    """
    settings = _email_settings_with_env(settings)
    provider = str(settings.get("email_provider") or "manual").strip().lower()
    delivery_enabled = bool(settings.get("email_delivery_enabled"))
    to_email = str(item.get("recipient_email") or "").strip()
    subject = str(item.get("subject") or "RiceMap24 notification")[:240]
    body = str(item.get("body") or "")
    from_name = str(settings.get("email_from_name") or "RiceMap24").strip()
    from_email = str(settings.get("email_from_email") or "no-reply@ricemap24.com").strip()
    reply_to = str(settings.get("email_reply_to") or from_email).strip()
    details = dict(item.get("details") or {})
    details.update({"provider": provider, "send_attempted_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"})
    if not to_email:
        details["send_error"] = "Missing recipient email"
        updated = mark_admin_notification_status(int(item["id"]), "error", details=details)
        return {"ok": False, "status": "error", "item": updated, "message": "Missing recipient email"}
    try:
        if (not delivery_enabled) or provider in {"", "manual", "queue", "queue_only"}:
            details["delivery_mode"] = "queue_only_simulation"
            details["email_delivery_enabled"] = delivery_enabled
            details["message"] = "Marked as sent in safe queue-only mode. No real email was sent."
            updated = mark_admin_notification_status(int(item["id"]), "sent", details=details)
            return {"ok": True, "status": "sent", "item": updated, "message": details["message"]}
        if provider == "smtp":
            password = os.environ.get("RICEMAP24_SMTP_PASSWORD") or os.environ.get("SMTP_PASSWORD")
            host = str(settings.get("smtp_host") or "").strip()
            port = int(settings.get("smtp_port") or 587)
            username = str(settings.get("smtp_username") or from_email).strip()
            if not host or not password:
                raise RuntimeError("SMTP host/password secret missing")
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
            msg["To"] = to_email
            if reply_to:
                msg["Reply-To"] = reply_to
            msg.set_content(body or " ")
            if port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as smtp:
                    if username:
                        smtp.login(username, password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(host, port, timeout=20) as smtp:
                    smtp.starttls(context=ssl.create_default_context())
                    if username:
                        smtp.login(username, password)
                    smtp.send_message(msg)
            details["delivery_mode"] = "smtp"
            updated = mark_admin_notification_status(int(item["id"]), "sent", details=details)
            return {"ok": True, "status": "sent", "item": updated, "message": "Sent via SMTP"}
        if provider == "sendgrid":
            api_key = os.environ.get("RICEMAP24_SENDGRID_API_KEY") or os.environ.get("SENDGRID_API_KEY")
            if not api_key:
                raise RuntimeError("SendGrid API key secret missing")
            payload = {"personalizations":[{"to":[{"email":to_email}]}],"from":{"email":from_email,"name":from_name or "RiceMap24"},"subject":subject,"content":[{"type":"text/plain","value":body or " "}]}
            r = httpx.post("https://api.sendgrid.com/v3/mail/send", headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}, json=payload, timeout=20)
            if r.status_code >= 300:
                raise RuntimeError(f"SendGrid error {r.status_code}: {r.text[:300]}")
            details["delivery_mode"] = "sendgrid"
            updated = mark_admin_notification_status(int(item["id"]), "sent", details=details)
            return {"ok": True, "status": "sent", "item": updated, "message": "Sent via SendGrid"}
        if provider == "postmark":
            token = os.environ.get("RICEMAP24_POSTMARK_SERVER_TOKEN") or os.environ.get("POSTMARK_SERVER_TOKEN")
            if not token:
                raise RuntimeError("Postmark server token secret missing")
            payload = {"From": f"{from_name} <{from_email}>" if from_name else from_email, "To": to_email, "Subject": subject, "TextBody": body or " ", "ReplyTo": reply_to or from_email}
            r = httpx.post("https://api.postmarkapp.com/email", headers={"X-Postmark-Server-Token": token, "Content-Type":"application/json", "Accept":"application/json"}, json=payload, timeout=20)
            if r.status_code >= 300:
                raise RuntimeError(f"Postmark error {r.status_code}: {r.text[:300]}")
            details["delivery_mode"] = "postmark"
            updated = mark_admin_notification_status(int(item["id"]), "sent", details=details)
            return {"ok": True, "status": "sent", "item": updated, "message": "Sent via Postmark"}
        raise RuntimeError(f"Unknown email provider: {provider}")
    except Exception as exc:
        details["send_error"] = str(exc)
        updated = mark_admin_notification_status(int(item["id"]), "error", details=details)
        return {"ok": False, "status": "error", "item": updated, "message": str(exc)}


def _notification_target_email(recipient_type: str = "admin", listing: Optional[dict] = None) -> str:
    settings = _email_settings_with_env(get_admin_settings())
    if recipient_type == "owner" and listing:
        contact = listing.get("contact") or {}
        if isinstance(contact, dict) and str(contact.get("email") or "").strip():
            return str(contact.get("email") or "").strip()
    return str(settings.get("admin_notification_email") or "").strip()


def _maybe_queue_notification(notification_type: str, *, subject: str, body: str, recipient_type: str = "admin", listing: Optional[dict] = None, listing_id: Optional[int] = None, ticket_id: Optional[int] = None, details: Optional[dict] = None) -> None:
    settings = get_admin_settings()
    if not settings.get("email_notifications_enabled", True):
        return
    type_key = {
        "new_ticket": "notify_new_tickets",
        "admin_reply": "notify_admin_replies",
        "trial_expiry": "notify_trial_expiry",
        "overdue_payment": "notify_overdue_payment",
    }.get(notification_type)
    if type_key and not settings.get(type_key, True):
        return
    try:
        queue_admin_notification(
            notification_type,
            recipient_type=recipient_type,
            recipient_email=_notification_target_email(recipient_type, listing),
            subject=subject,
            body=body,
            listing_id=listing_id if listing_id is not None else (int(listing["id"]) if listing and listing.get("id") else None),
            ticket_id=ticket_id,
            details=details or {},
            status="queued",
        )
    except Exception:
        pass


# --- Stripe webhook event admin log helpers (safe local fallback) -----------
def _ensure_stripe_webhook_events_table() -> None:
    """Create/upgrade the local Stripe webhook event table.

    The db module owns the normal migration, but this fallback keeps older local
    SQLite files from crashing when a newer admin UI asks for webhook events.
    """
    try:
        with connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stripe_webhook_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    event_id TEXT,
                    event_type TEXT,
                    listing_id INTEGER,
                    subscription_id TEXT,
                    customer_id TEXT,
                    status TEXT NOT NULL DEFAULT 'received',
                    source TEXT DEFAULT 'webhook',
                    message TEXT DEFAULT '',
                    details_json TEXT DEFAULT '{}',
                    payload_json TEXT DEFAULT '{}'
                )
                """
            )
            cols = {r[1] for r in conn.execute("PRAGMA table_info(stripe_webhook_events)").fetchall()}
            for name, ddl in {
                'listing_id': 'INTEGER',
                'subscription_id': 'TEXT',
                'customer_id': 'TEXT',
                'details_json': "TEXT DEFAULT '{}'",
                'payload_json': "TEXT DEFAULT '{}'",
            }.items():
                if name not in cols:
                    try:
                        conn.execute(f"ALTER TABLE stripe_webhook_events ADD COLUMN {name} {ddl}")
                    except Exception:
                        pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stripe_events_created ON stripe_webhook_events(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stripe_events_type ON stripe_webhook_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stripe_events_listing ON stripe_webhook_events(listing_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stripe_events_event_id ON stripe_webhook_events(event_id)")
            conn.commit()
    except Exception:
        pass


def _stripe_event_already_seen(event_id: str) -> bool:
    if not event_id:
        return False
    try:
        _ensure_stripe_webhook_events_table()
        with connect() as conn:
            row = conn.execute(
                "SELECT id FROM stripe_webhook_events WHERE event_id=? AND status IN ('processed','ignored','error') LIMIT 1",
                (str(event_id),),
            ).fetchone()
            return bool(row)
    except Exception:
        return False


def record_stripe_webhook_event(*args, **kwargs) -> None:
    """Best-effort Stripe webhook event logger.

    Accepts both old local call style and the db.py call style:
    record_stripe_webhook_event(event_type, event_id=..., listing_id=..., details=...)
    """
    try:
        _ensure_stripe_webhook_events_table()
        event_type = str(kwargs.pop('event_type', '') or '')
        event_id = str(kwargs.pop('event_id', '') or kwargs.pop('stripe_event_id', '') or '')
        if args:
            first = str(args[0] or '')
            # Stripe event types contain dots; ids usually start with evt_.
            if first.startswith('evt_') and not event_id:
                event_id = first
            elif not event_type:
                event_type = first
            elif not event_id:
                event_id = first
        status = str(kwargs.pop('status', 'received') or 'received')[:40]
        source = str(kwargs.pop('source', 'webhook') or 'webhook')[:40]
        message = str(kwargs.pop('message', '') or kwargs.pop('error', '') or '')[:500]
        listing_id = kwargs.pop('listing_id', None)
        subscription_id = str(kwargs.pop('subscription_id', '') or '')[:160]
        customer_id = str(kwargs.pop('customer_id', '') or '')[:160]
        details = kwargs.pop('details', None)
        payload = kwargs.pop('payload', None)
        if details is None:
            details = kwargs
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO stripe_webhook_events
                (event_id, event_type, listing_id, subscription_id, customer_id, status, source, message, details_json, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id[:160],
                    event_type[:160],
                    int(listing_id) if listing_id else None,
                    subscription_id,
                    customer_id,
                    status,
                    source,
                    message,
                    json.dumps(details or {}, ensure_ascii=False, default=str),
                    json.dumps(payload or {}, ensure_ascii=False, default=str),
                ),
            )
            conn.commit()
    except Exception:
        pass


def list_stripe_webhook_events(limit: int = 80, status: str = 'all', event_type: str = 'all', q: str = '') -> list[dict]:
    """Return Stripe webhook events for the admin UI, or an empty list if none exist yet."""
    try:
        _ensure_stripe_webhook_events_table()
        try:
            lim = max(1, min(int(limit or 80), 300))
        except Exception:
            lim = 80
        clauses = []
        params = []
        if status and status != 'all':
            clauses.append('LOWER(status) = LOWER(?)')
            params.append(str(status))
        if event_type and event_type != 'all':
            clauses.append('LOWER(event_type) = LOWER(?)')
            params.append(str(event_type))
        if q:
            clauses.append('(event_id LIKE ? OR event_type LIKE ? OR message LIKE ? OR subscription_id LIKE ? OR customer_id LIKE ? OR details_json LIKE ? OR payload_json LIKE ?)')
            needle = f"%{q}%"
            params.extend([needle, needle, needle, needle, needle, needle, needle])
        where = (' WHERE ' + ' AND '.join(clauses)) if clauses else ''
        with connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id, created_at, event_id, event_type, listing_id, subscription_id, customer_id, status, source, message, details_json, payload_json
                FROM stripe_webhook_events
                {where}
                ORDER BY id DESC
                LIMIT ?
                """,
                [*params, lim],
            ).fetchall()
        items = []
        for r in rows:
            d = dict(r)
            for field in ('details_json', 'payload_json'):
                raw = d.pop(field, '{}') or '{}'
                try:
                    d[field.replace('_json', '')] = json.loads(raw)
                except Exception:
                    d[field.replace('_json', '')] = {}
            items.append(d)
        return items
    except Exception:
        return []


def _stripe_ts_to_date(value) -> Optional[str]:
    try:
        if value:
            return datetime.utcfromtimestamp(int(value)).strftime('%Y-%m-%d')
    except Exception:
        return None
    return None


def _stripe_subscription_period_end(obj: dict) -> Optional[str]:
    if not isinstance(obj, dict):
        return None
    return _stripe_ts_to_date(obj.get('current_period_end') or obj.get('period_end'))


@app.post("/api/admin/billing/sync")
def admin_billing_sync(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    changed = refresh_billing_visibility()
    try:
        log_admin_activity("billing_visibility_sync", entity_type="billing", title="Synced billing visibility", details={"changed": changed})
    except Exception:
        pass
    return {"ok": True, "changed": changed}




@app.get("/api/admin/stripe/events")
def admin_stripe_events(request: Request, key: Optional[str] = None, status: str = "all", event_type: str = "all", q: str = "", limit: int = 80):
    _require_admin(key, request=request)
    return {"items": list_stripe_webhook_events(limit=limit, status=status, event_type=event_type, q=q)}


@app.get("/api/admin/stripe/config")
def admin_stripe_config(request: Request, key: Optional[str] = None):
    _require_admin(key, request=request)
    return _stripe_public_status_for_admin()


@app.post("/api/admin/stripe/simulate")
def admin_stripe_simulate(payload: dict, request: Request, key: Optional[str] = None):
    """Admin/dev helper: simulate the Stripe subscription events that production webhooks will send.

    This does not contact Stripe. It updates the same billing/access fields used by the admin UI
    so the paid, past_due and cancelled flows can be tested locally before real webhook setup.
    """
    _check_admin(key, request=request)
    p = payload or {}
    try:
        listing_id = int(p.get("listing_id") or 0)
    except Exception:
        listing_id = 0
    if not listing_id:
        raise HTTPException(status_code=400, detail="Missing listing_id")
    event_type = str(p.get("event_type") or "invoice.paid").strip().lower()
    listing = get_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    sub_id = str(listing.get("stripe_subscription_id") or p.get("subscription_id") or f"sub_dev_{listing_id}")
    customer_id = str(listing.get("stripe_customer_id") or p.get("customer_id") or f"cus_dev_{listing_id}")
    period_end = str(p.get("current_period_end") or listing.get("paid_until") or (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"))

    if event_type in ("checkout.session.completed", "invoice.paid", "customer.subscription.active", "subscription.active", "paid"):
        stripe_mark_subscription_active(
            listing_id=listing_id,
            customer_id=customer_id,
            subscription_id=sub_id,
            status="active",
            current_period_end=period_end,
        )
        admin_update_meta(listing_id, account_status="active", paid_status="paid", paid_until=period_end, plan_active=1)
        action = "stripe_simulate_paid"
        title = "Simulated Stripe paid event"
    elif event_type in ("invoice.payment_failed", "customer.subscription.past_due", "past_due"):
        # Ensure there is a subscription id to attach the simulated inactive event to.
        if not listing.get("stripe_subscription_id"):
            stripe_mark_subscription_active(listing_id, customer_id=customer_id, subscription_id=sub_id, status="active", current_period_end=period_end)
        stripe_mark_inactive_by_subscription(sub_id, status="past_due")
        admin_update_meta(listing_id, account_status="past_due", paid_status="unpaid", plan_active=0)
        action = "stripe_simulate_past_due"
        title = "Simulated Stripe past_due event"
        _maybe_queue_notification(
            "overdue_payment",
            subject=f"Payment past due: {listing.get('name') or listing_id}",
            body=f"Stripe simulation marked {listing.get('name') or listing_id} as past_due/unpaid.",
            recipient_type="admin",
            listing=listing,
            details={"event_type": event_type, "subscription_id": sub_id},
        )
    elif event_type in ("customer.subscription.deleted", "customer.subscription.cancelled", "cancelled", "canceled"):
        if not listing.get("stripe_subscription_id"):
            stripe_mark_subscription_active(listing_id, customer_id=customer_id, subscription_id=sub_id, status="active", current_period_end=period_end)
        stripe_mark_inactive_by_subscription(sub_id, status="cancelled")
        admin_update_meta(listing_id, account_status="cancelled", paid_status="unpaid", plan_active=0)
        action = "stripe_simulate_cancelled"
        title = "Simulated Stripe cancelled event"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported event_type: {event_type}")

    changed = refresh_billing_visibility(listing_id=listing_id)
    after = get_by_id(listing_id) or {}
    try:
        log_admin_activity(
            action,
            entity_type="stripe",
            entity_id=listing_id,
            listing_id=listing_id,
            customer_no=after.get("customer_no") or "",
            title=title,
            details={"event_type": event_type, "subscription_id": sub_id, "billing_visibility_changed": changed},
        )
    except Exception:
        pass
    return {"ok": True, "listing": after, "event_type": event_type, "billing_visibility_changed": changed}


@app.post("/api/admin/listings/{listing_id}/update")
def admin_update_listing(listing_id: int, payload: dict, request: Request, key: Optional[str] = None):
    """Update admin-managed fields: plan/billing/paid/note.

    Payload:
      - plan: basic|premium
      - billing: monthly|yearly
      - plan_active: 0|1
      - admin_note: str
      - paid_status: unpaid|paid
      - paid_until: ISO-ish str (free text)
    """
    _check_admin(key, request=request)
    p = payload or {}
    before = None
    try:
        before = get_by_id(listing_id)
    except Exception:
        before = None
    try:
        admin_update_meta(
            listing_id,
            plan=p.get("plan"),
            billing=p.get("billing"),
            plan_active=p.get("plan_active"),
            admin_note=p.get("admin_note"),
            paid_status=p.get("paid_status"),
            paid_until=p.get("paid_until"),
            account_status=p.get("account_status") if "account_status" in p else None,
            access_type=p.get("access_type") if "access_type" in p else None,
            access_expires_at=p.get("access_expires_at") if "access_expires_at" in p else None,
            access_reason=p.get("access_reason") if "access_reason" in p else None,
            feature_overrides=p.get("feature_overrides") if "feature_overrides" in p else None,
        )
        try:
            after = get_by_id(listing_id)
            changed = {}
            for k in ["plan", "billing", "plan_active", "admin_note", "paid_status", "paid_until", "account_status", "access_type", "access_expires_at", "access_reason", "feature_overrides"]:
                if k in p:
                    changed[k] = {"from": (before or {}).get(k), "to": (after or {}).get(k)}
            log_admin_activity(
                "listing_update",
                entity_type="listing",
                entity_id=listing_id,
                listing_id=listing_id,
                customer_no=(after or {}).get("customer_no") or "",
                title=(after or {}).get("name") or f"Listing {listing_id}",
                details={"changed": changed, "patch_keys": list(p.keys())},
            )
        except Exception:
            pass
        return {"ok": True}
    except KeyError:
        raise HTTPException(status_code=404, detail="Not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/admin/listings/{listing_id}/activate")
def admin_activate_listing(listing_id: int, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    try:
        slug = admin_activate(listing_id)

        # Best-effort: if the listing has no coords yet, try to geocode from postcode/city/country.
        try:
            item = get_by_id(listing_id)
            if item and (item.get("lat") is None or item.get("lng") is None):
                parts = []
                if item.get("postcode"): parts.append(str(item.get("postcode")).strip())
                if item.get("city"): parts.append(str(item.get("city")).strip())
                if item.get("country"): parts.append(str(item.get("country")).strip())
                q = " ".join([p for p in parts if p])
                if q:
                    g = geocode(q=q, country=(item.get("country") or None))  # reuse endpoint logic
                    if isinstance(g, dict) and g.get("ok"):
                        item["lat"] = g.get("lat")
                        item["lng"] = g.get("lng")
                        update_draft(listing_id, item)
        except Exception:
            pass

        try:
            item = get_by_id(listing_id)
            log_admin_activity("listing_activate", entity_type="listing", entity_id=listing_id, listing_id=listing_id, customer_no=(item or {}).get("customer_no") or "", title=(item or {}).get("name") or f"Listing {listing_id}", details={"slug": slug})
        except Exception:
            pass
        return {"ok": True, "slug": slug}
    except KeyError:
        raise HTTPException(status_code=404, detail="Not found")


@app.post("/api/admin/listings/{listing_id}/deactivate")
def admin_deactivate_listing(listing_id: int, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    try:
        admin_deactivate(listing_id)
        try:
            item = get_by_id(listing_id)
            log_admin_activity("listing_deactivate", entity_type="listing", entity_id=listing_id, listing_id=listing_id, customer_no=(item or {}).get("customer_no") or "", title=(item or {}).get("name") or f"Listing {listing_id}")
        except Exception:
            pass
        return {"ok": True}
    except KeyError:
        raise HTTPException(status_code=404, detail="Not found")


@app.post("/api/admin/listings/{listing_id}/restore")
def admin_restore_deleted_listing(listing_id: int, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    try:
        restored = restore_deleted_listing_by_admin(listing_id)
        try:
            log_admin_activity("listing_restore", entity_type="listing", entity_id=listing_id, listing_id=listing_id, customer_no=(restored or {}).get("customer_no") or "", title=(restored or {}).get("name") or f"Listing {listing_id}", details={"from": "deleted_by_request"})
        except Exception:
            pass
        return {"ok": True, "listing": restored}
    except KeyError:
        raise HTTPException(status_code=404, detail="Not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# --- Support tickets (owner + admin MVP) ---
@app.get("/api/owner/{token}/tickets")
def owner_list_tickets(token: str):
    if not get_admin_settings().get("support_tickets_enabled", True):
        raise HTTPException(status_code=403, detail="Support tickets are currently disabled")
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    items = list_support_tickets(listing_id=int(listing["id"]), status="all")
    return {"items": items, "count": len(items)}


@app.post("/api/owner/{token}/tickets")
def owner_create_ticket(token: str, payload: dict):
    if not get_admin_settings().get("support_tickets_enabled", True):
        raise HTTPException(status_code=403, detail="Support tickets are currently disabled")
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    p = payload or {}
    try:
        ticket = create_support_ticket(
            listing_id=int(listing["id"]),
            subject=str(p.get("subject") or ""),
            body=str(p.get("body") or ""),
            category=str(p.get("category") or "general"),
            created_by="owner",
        )
        _maybe_queue_notification(
            "new_ticket",
            subject=f"New support ticket: {ticket.get('subject') or 'No subject'}",
            body=f"{listing.get('name') or 'Kitchen'} opened a support ticket. Category: {ticket.get('category') or 'general'}",
            recipient_type="admin",
            listing=listing,
            ticket_id=int(ticket.get("id") or 0),
            details={"category": ticket.get("category"), "priority": ticket.get("priority")},
        )
        return {"ok": True, "ticket": ticket}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/owner/{token}/tickets/{ticket_id}")
def owner_get_ticket(token: str, ticket_id: int):
    if not get_admin_settings().get("support_tickets_enabled", True):
        raise HTTPException(status_code=403, detail="Support tickets are currently disabled")
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    ticket = get_support_ticket(ticket_id)
    if not ticket or int(ticket.get("listing_id") or 0) != int(listing["id"]):
        raise HTTPException(status_code=404, detail="Ticket not found")
    # Owner must not see internal admin notes/messages.
    ticket = dict(ticket)
    ticket["internal_note"] = ""
    ticket["messages"] = [m for m in (ticket.get("messages") or []) if not int(m.get("is_internal") or 0)]
    return {"ticket": ticket}


@app.post("/api/owner/{token}/tickets/{ticket_id}/reply")
def owner_reply_ticket(token: str, ticket_id: int, payload: dict):
    if not get_admin_settings().get("support_tickets_enabled", True):
        raise HTTPException(status_code=403, detail="Support tickets are currently disabled")
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    ticket = get_support_ticket(ticket_id)
    if not ticket or int(ticket.get("listing_id") or 0) != int(listing["id"]):
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        updated = add_support_ticket_message(ticket_id, "owner", str((payload or {}).get("body") or ""), 0)
        _maybe_queue_notification(
            "new_ticket",
            subject=f"New owner reply: {updated.get('subject') or 'Support ticket'}",
            body=f"{listing.get('name') or 'Kitchen'} replied to support ticket #{ticket_id}.",
            recipient_type="admin",
            listing=listing,
            ticket_id=int(ticket_id),
            details={"reply": True},
        )
        updated["internal_note"] = ""
        updated["messages"] = [m for m in (updated.get("messages") or []) if not int(m.get("is_internal") or 0)]
        return {"ok": True, "ticket": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/admin/tickets")
def admin_tickets(request: Request, key: Optional[str] = None, status: str = "all"):
    _check_admin(key, request=request)
    items = list_support_tickets(status=status)
    return {"items": items, "count": len(items)}


@app.get("/api/admin/tickets/{ticket_id}")
def admin_ticket_detail(ticket_id: int, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    ticket = get_support_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"ticket": ticket}


@app.post("/api/admin/tickets/{ticket_id}/reply")
def admin_ticket_reply(ticket_id: int, payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    p = payload or {}
    try:
        ticket = add_support_ticket_message(ticket_id, "admin", str(p.get("body") or ""), 1 if p.get("is_internal") else 0)
        if not p.get("is_internal"):
            listing = get_by_id(int(ticket.get("listing_id") or 0)) if ticket.get("listing_id") else None
            _maybe_queue_notification(
                "admin_reply",
                subject=f"RiceMap24 support replied: {ticket.get('subject') or 'Support ticket'}",
                body=str(p.get("body") or ""),
                recipient_type="owner",
                listing=listing,
                ticket_id=int(ticket_id),
                details={"ticket_id": ticket_id},
            )
        try:
            log_admin_activity("ticket_reply", entity_type="support_ticket", entity_id=ticket_id, listing_id=ticket.get("listing_id"), customer_no=ticket.get("listing_customer_no") or "", title=ticket.get("subject") or f"Ticket {ticket_id}", details={"is_internal": bool(p.get("is_internal"))})
        except Exception:
            pass
        return {"ok": True, "ticket": ticket}
    except KeyError:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/admin/tickets/{ticket_id}/update")
def admin_ticket_update(ticket_id: int, payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    p = payload or {}
    try:
        ticket = update_support_ticket(
            ticket_id,
            status=p.get("status"),
            priority=p.get("priority"),
            internal_note=p.get("internal_note") if "internal_note" in p else None,
            builder_stage=p.get("builder_stage"),
            builder_recommended_plan=p.get("builder_recommended_plan") if "builder_recommended_plan" in p else None,
            builder_payment_status=p.get("builder_payment_status"),
        )
        try:
            log_admin_activity("ticket_update", entity_type="support_ticket", entity_id=ticket_id, listing_id=ticket.get("listing_id"), customer_no=ticket.get("listing_customer_no") or "", title=ticket.get("subject") or f"Ticket {ticket_id}", details={"status": p.get("status"), "priority": p.get("priority"), "builder_stage": p.get("builder_stage"), "builder_payment_status": p.get("builder_payment_status"), "internal_note_changed": "internal_note" in p})
        except Exception:
            pass
        return {"ok": True, "ticket": ticket}
    except KeyError:
        raise HTTPException(status_code=404, detail="Ticket not found")




@app.get("/api/admin/users")
def admin_users(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return {"items": list_admin_users()}


@app.post("/api/admin/users")
def admin_create_user(payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    try:
        user = upsert_admin_user(payload or {})
        try:
            log_admin_activity("admin_user_create", actor=str(user.get("email") or user.get("name") or "admin"), entity_type="admin_user", entity_id=user.get("id"), title=user.get("name") or "Admin user", details={"role": user.get("role"), "active": bool(user.get("active"))})
        except Exception:
            pass
        return {"ok": True, "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/admin/users/{user_id}")
def admin_update_user(user_id: int, payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    try:
        user = upsert_admin_user(payload or {}, user_id=user_id)
        try:
            log_admin_activity("admin_user_update", actor=str(user.get("email") or user.get("name") or "admin"), entity_type="admin_user", entity_id=user_id, title=user.get("name") or f"Admin user {user_id}", details={"role": user.get("role"), "active": bool(user.get("active"))})
        except Exception:
            pass
        return {"ok": True, "user": user}
    except KeyError:
        raise HTTPException(status_code=404, detail="Admin user not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/admin/users/{user_id}/seen")
def admin_mark_user_seen(user_id: int, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    mark_admin_user_seen(user_id)
    try:
        log_admin_activity("admin_login_seen", actor=f"admin_user:{user_id}", entity_type="admin_user", entity_id=user_id, title=f"Admin user {user_id}")
    except Exception:
        pass
    return {"ok": True}


@app.get("/api/admin/activity")
def admin_activity(request: Request, key: Optional[str] = None, limit: int = 100, action: str = "all", q: str = ""):
    _check_admin(key, request=request)
    return {"items": list_admin_activity_log(limit=limit, action=action, q=q)}



@app.get("/api/admin/announcements")
def admin_announcements(request: Request, key: Optional[str] = None, status: str = "all", target_plan: str = "all", limit: int = 120):
    _check_admin(key, request=request)
    return {"items": list_admin_announcements(limit=limit, status=status, target_plan=target_plan)}


@app.post("/api/admin/announcements")
def admin_create_announcement(payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    try:
        item = create_admin_announcement(payload or {})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        log_admin_activity("announcement_create", actor="admin", entity_type="admin_announcement", entity_id=item.get("id"), title=item.get("title"), details={"target_plan": item.get("target_plan"), "target_listing_id": item.get("target_listing_id"), "status": item.get("status")})
    except Exception:
        pass
    return {"ok": True, "item": item}


@app.post("/api/admin/announcements/{announcement_id}/status")
def admin_announcement_status(announcement_id: int, payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    status = str((payload or {}).get("status") or "active")
    item = set_admin_announcement_status(int(announcement_id), status)
    try:
        log_admin_activity("announcement_status", actor="admin", entity_type="admin_announcement", entity_id=int(announcement_id), title=item.get("title"), details={"status": item.get("status")})
    except Exception:
        pass
    return {"ok": True, "item": item}


@app.get("/api/admin/notifications")
def admin_notifications(request: Request, key: Optional[str] = None, status: str = "all", notification_type: str = "all", q: str = "", limit: int = 120):
    _check_admin(key, request=request)
    return {"items": list_admin_notifications(limit=limit, status=status, notification_type=notification_type, q=q)}


@app.post("/api/admin/notifications/{notification_id}/status")
def admin_notification_status(notification_id: int, payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    p = payload or {}
    status = str(p.get("status") or "queued")
    if status not in {"queued", "sent", "skipped", "error"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    item = mark_admin_notification_status(notification_id, status, details=p.get("details") if isinstance(p.get("details"), dict) else {})
    try:
        log_admin_activity("notification_status", entity_type="admin_notification", entity_id=notification_id, title=item.get("subject") or f"Notification {notification_id}", details={"status": status})
    except Exception:
        pass
    return {"ok": True, "item": item}




@app.post("/api/admin/notifications/{notification_id}/send")
def admin_send_notification(notification_id: int, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    item = get_admin_notification(int(notification_id))
    if not item:
        raise HTTPException(status_code=404, detail="Notification not found")
    if str(item.get("status") or "queued") != "queued":
        raise HTTPException(status_code=400, detail="Only queued notifications can be sent")
    result = _send_admin_notification_item(item, get_admin_settings())
    try:
        log_admin_activity("notification_send", entity_type="admin_notification", entity_id=notification_id, title=item.get("subject") or f"Notification {notification_id}", details={"ok": result.get("ok"), "status": result.get("status"), "message": result.get("message")})
    except Exception:
        pass
    return result


@app.post("/api/admin/notifications/send-batch")
def admin_send_notification_batch(request: Request, payload: dict = None, key: Optional[str] = None):
    _check_admin(key, request=request)
    p = payload or {}
    ids = p.get("ids") or []
    if not isinstance(ids, list):
        raise HTTPException(status_code=400, detail="ids must be a list")
    settings = get_admin_settings()
    results = []
    for raw_id in ids[:200]:
        try:
            item = get_admin_notification(int(raw_id))
            if not item or str(item.get("status") or "queued") != "queued":
                continue
            results.append(_send_admin_notification_item(item, settings))
        except Exception as exc:
            results.append({"ok": False, "status": "error", "message": str(exc), "id": raw_id})
    sent = sum(1 for r in results if r.get("status") == "sent")
    errors = sum(1 for r in results if r.get("status") == "error")
    try:
        log_admin_activity("notification_send_batch", entity_type="admin_notification", title="Sent notification batch", details={"requested": len(ids), "sent": sent, "errors": errors})
    except Exception:
        pass
    return {"ok": errors == 0, "sent": sent, "errors": errors, "results": results}


@app.post("/api/admin/notifications/generate-trial-expiry")
def admin_generate_trial_expiry_notifications(request: Request, payload: dict = None, key: Optional[str] = None):
    _check_admin(key, request=request)
    p = payload or {}
    try:
        days = int(p.get("days") or 7)
    except Exception:
        days = 7
    created = queue_due_access_notifications(days_ahead=days)
    try:
        log_admin_activity("notification_generate_trial_expiry", entity_type="admin_notification", title="Generated trial/access expiry notifications", details={"days": days, "created": created})
    except Exception:
        pass
    return {"ok": True, "created": created}


@app.post("/api/admin/notifications/test-email")
def admin_test_email_notification(request: Request, payload: dict = None, key: Optional[str] = None):
    """Queue a test email notification from the current email provider settings."""
    _check_admin(key, request=request)
    settings = get_admin_settings()
    p = payload or {}
    recipient = str(p.get("recipient_email") or settings.get("admin_notification_email") or "").strip()
    provider = str(settings.get("email_provider") or "manual").strip()
    from_name = str(settings.get("email_from_name") or "RiceMap24").strip()
    from_email = str(settings.get("email_from_email") or "").strip()
    send_now = bool(p.get("send_now"))
    email_cfg = _email_config_snapshot(settings)
    item = queue_admin_notification(
        "email_provider_test",
        recipient_type="admin",
        recipient_email=recipient,
        subject="RiceMap24 test email configuration",
        body=(
            "This is a test notification from RiceMap24 admin. "
            f"Provider: {provider}. From: {from_name} <{from_email}>. "
            "If real delivery is enabled and provider secrets are configured, this message can be sent from the queue."
        ),
        details={"provider": provider, "from_name": from_name, "from_email": from_email, "mode": "queued_email_test", "email_config": email_cfg},
        status="queued",
    )
    result = {"ok": True, "item": item, "email_config": email_cfg}
    if send_now:
        result = _send_admin_notification_item(item, settings)
        result["email_config"] = email_cfg
    try:
        log_admin_activity("notification_test_email", entity_type="admin_notification", entity_id=item.get("id"), title="Queued test email notification", details={"recipient": recipient, "provider": provider, "send_now": send_now, "ready_for_real_delivery": email_cfg.get("ready_for_real_delivery")})
    except Exception:
        pass
    return result



# --- Admin owner communications / email templates --------------------------
OWNER_EMAIL_TEMPLATES = [
    {
        "key": "welcome_new_owner",
        "name": "Welcome email",
        "category": "onboarding",
        "email_kind": "transactional",
        "subject": "Welcome to RiceMap24 — start building your kitchen page",
        "body": "Hi {owner_name},\n\nWelcome to RiceMap24.\n\nYour kitchen page has been created. The next step is to make it clear, trustworthy and ready for customers before you publish it.\n\nStart with these steps:\n1. Add a strong hero image.\n2. Add your dishes, descriptions and prices.\n3. Check your city, country and contact details.\n4. Preview your public kitchen page.\n5. Publish when you are ready.\n\nOpen your dashboard:\n{dashboard_link}\n\nNeed help?\nOpen a support ticket inside your RiceMap24 dashboard:\n{support_ticket_link}\n\nPlease do not reply to this email."
    },
    {
        "key": "complete_kitchen_page",
        "name": "Complete kitchen page",
        "category": "onboarding",
        "email_kind": "transactional",
        "subject": "Complete your RiceMap24 kitchen page",
        "body": "Hi {owner_name},\n\nYour RiceMap24 kitchen page has been created, but it is not ready to publish yet.\n\nBefore customers can discover {kitchen_name}, we recommend completing these steps:\n1. Add a strong hero image.\n2. Add your dishes and descriptions.\n3. Check your city and contact details.\n4. Preview your public kitchen page.\n5. Publish when you are ready.\n\nOpen your dashboard:\n{dashboard_link}\n\nNeed help?\nOpen a support ticket inside your RiceMap24 dashboard:\n{support_ticket_link}\n\nPlease do not reply to this email."
    },
    {
        "key": "ready_to_publish",
        "name": "Ready to publish",
        "category": "onboarding",
        "email_kind": "transactional",
        "subject": "Your RiceMap24 kitchen page is ready to publish",
        "body": "Hi {owner_name},\n\n{kitchen_name} now has the main content needed for a public kitchen page.\n\nBefore publishing, we recommend one final check:\n1. Does your hero image show your food clearly?\n2. Are your dish names easy to understand?\n3. Are your descriptions clear and helpful?\n4. Is your location information correct?\n5. Does your page look trustworthy to a new customer?\n\nWhen you are ready, you can publish your kitchen page from your dashboard.\n\nOpen your dashboard:\n{dashboard_link}\n\nNeed help?\nOpen a support ticket inside your RiceMap24 dashboard:\n{support_ticket_link}\n\nPlease do not reply to this email."
    },
    {
        "key": "kitchen_published",
        "name": "Kitchen published / live",
        "category": "onboarding",
        "email_kind": "transactional",
        "subject": "Your RiceMap24 kitchen page is now live",
        "body": "Hi {owner_name},\n\n{kitchen_name} is now published on RiceMap24.\n\nCustomers can now discover your kitchen page, see your dishes and use your page to place interest or orders according to your setup.\n\nRecommended next steps:\n1. Open your public kitchen page.\n2. Share your kitchen link on social media.\n3. Use your QR poster from the dashboard.\n4. Tell existing customers where to find your menu.\n5. Keep your dishes and photos updated.\n\nPublic kitchen page:\n{public_kitchen_link}\n\nOpen your dashboard:\n{dashboard_link}\n\nNeed help?\nOpen a support ticket inside your RiceMap24 dashboard:\n{support_ticket_link}\n\nPlease do not reply to this email."
    },
    {
        "key": "first_orders_tip",
        "name": "First orders tip",
        "category": "marketing",
        "email_kind": "marketing",
        "subject": "How to get your first RiceMap24 orders",
        "body": "Hi {owner_name},\n\nNow that {kitchen_name} is being set up, the next step is to help people understand what they can order and when.\n\nA simple first-order routine works best:\n1. Choose 1–3 dishes you can make consistently.\n2. Set a clear pickup day or pickup window.\n3. Share one clear message with your public kitchen page link.\n\nExample message:\nHomemade food available for preorder. See menu and order here: {public_kitchen_link}\n\nDo not try to market everything at once. Make it easy to understand what customers can order this week.\n\nOpen your dashboard:\n{dashboard_link}\n\nNeed help?\nOpen a support ticket inside your RiceMap24 dashboard:\n{support_ticket_link}\n\nPlease do not reply to this email."
    },
    {
        "key": "qr_poster_reminder",
        "name": "QR / poster reminder",
        "category": "marketing",
        "email_kind": "marketing",
        "subject": "Use your QR poster to bring customers to your kitchen page",
        "body": "Hi {owner_name},\n\nA simple QR poster can help more people find {kitchen_name}.\n\nYou can place it where potential customers already see you:\n1. At pickup.\n2. In local shops, if allowed.\n3. At local events.\n4. In community spaces.\n5. Together with food deliveries or samples.\n\nYour poster should have one clear purpose: make it easy for people to open your kitchen page and see your food.\n\nOpen Print & Promo tools:\n{print_tools_link}\n\nPublic kitchen page:\n{public_kitchen_link}\n\nNeed help?\nOpen a support ticket inside your RiceMap24 dashboard:\n{support_ticket_link}\n\nPlease do not reply to this email."
    },
    {
        "key": "new_content_available",
        "name": "New Business Academy content",
        "category": "content",
        "email_kind": "marketing",
        "subject": "New RiceMap24 content is ready for you",
        "body": "Hi {owner_name},\n\nNew content is now available in your RiceMap24 Business Academy.\n\nDepending on your plan, this may include Business Coach, Marketing Coach, Masterclass content or practical tools for improving your kitchen page and sales.\n\nYour current plan: {plan}\n\nOpen Business Academy:\n{business_academy_link}\n\nNeed help?\nOpen a support ticket inside your RiceMap24 dashboard:\n{support_ticket_link}\n\nPlease do not reply to this email."
    },
    {
        "key": "monthly_owner_update",
        "name": "Monthly owner update",
        "category": "news",
        "email_kind": "marketing",
        "subject": "RiceMap24 monthly update for kitchen owners",
        "body": "Hi {owner_name},\n\nHere is this month’s RiceMap24 Owner Update.\n\nEach month, RiceMap24 highlights one practical opportunity you can use to improve your kitchen page, customer communication or daily routines.\n\nOpen your RiceMap24 dashboard:\n{dashboard_link}\n\nThis is an automated RiceMap24 owner update.\nPlease do not reply to this email."
    },
    {
        "key": "trial_ending_owner",
        "name": "Trial ending",
        "category": "billing",
        "email_kind": "transactional",
        "subject": "Your RiceMap24 trial is ending soon",
        "body": "Hi {owner_name},\n\nYour RiceMap24 trial is ending soon.\n\nTo keep using your kitchen page and dashboard tools, please choose or confirm your subscription plan.\n\nYour current plan: {plan}\n\nOpen your dashboard:\n{dashboard_link}\n\nIf you do not continue, access to some features may be limited when the trial ends.\n\nNeed help?\nOpen a support ticket inside your RiceMap24 dashboard:\n{support_ticket_link}\n\nPlease do not reply to this email."
    },
]


MONTHLY_OWNER_UPDATE_THEMES = [{'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about the public kitchen page for {kitchen_name}. This is the page '
          'customers see when they open your RiceMap24 link from Explore, social media, QR posters or messages.\n'
          '\n'
          'Your public page should quickly answer three questions: What food do you make? What can customers order or '
          'preorder? Why does your kitchen feel trustworthy?\n'
          '\n'
          'Inside RiceMap24, use the Public Page / Edit Photos area to review the page the way a customer sees it. '
          'Focus especially on the top image, dish order, dish names, short descriptions and the overall first '
          'impression.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open your dashboard and go to Public Page.\n'
          '2. Preview the page as a customer, not as the owner.\n'
          '3. Check whether the hero image immediately shows food, kitchen style or your strongest offer.\n'
          '4. Move your strongest dishes higher on the page.\n'
          '5. Rewrite one or two unclear dish names or descriptions.\n'
          '6. Open your public kitchen link and check it on mobile.\n'
          '\n'
          'A small page improvement can make every future share, QR scan and social post work better. The page is the '
          'centre of your RiceMap24 presence.\n'
          '\n'
          'This is available in your current plan.\n'
          '\n'
          'Open your public kitchen page:\n'
          '{public_kitchen_link}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: use Public Page and Edit Photos to make the page look active and trustworthy.\n'
          '- Business: combine a clearer page with Print & Promo, so your QR poster sends people to a stronger kitchen '
          'page.\n'
          '- Growth: connect this work with Business Coach or Marketing Coach. Use the monthly guidance to decide what '
          'to improve next.\n'
          '- Pro: use BriteSight Photo Editor to improve food images before adding them to the page, and use '
          'BriteSight Design Studio if you want more polished visual material around your kitchen brand.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 1,
  'required_plan': 'basic',
  'subject': 'This month in RiceMap24: improve your public kitchen page',
  'title': 'Public page setup: make your kitchen page sell clearly'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about Print & Promo. This part of the app helps you turn your '
          'RiceMap24 page into simple offline marketing material with a QR code.\n'
          '\n'
          'For many home kitchens, customers discover the food offline first: at pickup, through friends, at a '
          'workplace, in a community space or at a small local event. A QR poster makes the next step easier. Instead '
          'of explaining the whole menu, you can point people to one clean kitchen page.\n'
          '\n'
          'Inside RiceMap24, Print & Promo is designed for simple materials such as QR posters and menu-style '
          'promotional assets. The main goal is not decoration. The goal is to help people open your kitchen page '
          'quickly.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open Tools, then Print & Promo.\n'
          '2. Create a QR poster for {kitchen_name}.\n'
          '3. Use a short message such as “See menu and preorder here”.\n'
          '4. Make sure the QR code is easy to scan.\n'
          '5. Print one version or save it as an image.\n'
          '6. Place it where customers naturally meet your food: pickup, samples, local events or workplace lunch '
          'conversations.\n'
          '\n'
          'The QR poster works best when the public kitchen page behind it is already clear. If needed, update your '
          'hero image and dish list before sharing the poster widely.\n'
          '\n'
          '{plan_access_note}\n'
          '\n'
          'Open Print & Promo:\n'
          '{print_tools_link}\n'
          '\n'
          'Open your public kitchen page:\n'
          '{public_kitchen_link}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: even without Print & Promo, keep using your public kitchen link in posts and messages.\n'
          '- Business: use Print & Promo to create QR material that points directly to your kitchen page.\n'
          '- Growth: use Marketing Coach to plan where and how often you share the QR poster, not just create it '
          'once.\n'
          '- Pro: use Pro Print Kit and BriteSight Design Studio to create more polished posters, cards and local '
          'promotional material with a stronger visual identity.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 2,
  'required_plan': 'business',
  'subject': 'This month in RiceMap24: use QR posters to bring customers online',
  'title': 'Print & Promo: use QR material to connect offline customers to your page'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about the photos on your kitchen page. Photos are not just '
          'decoration in RiceMap24. They help customers understand your food before they decide to order, preorder or '
          'contact you.\n'
          '\n'
          'The most important image is the hero image. It appears high on your kitchen page and helps shape the first '
          'impression. Dish photos also matter because they help customers compare options quickly. Clear photos can '
          'make the page feel more real and trustworthy.\n'
          '\n'
          'Inside the app, use the Public Page / Edit Photos area to review and improve your images. You do not need '
          'perfect restaurant photos. You need images that are bright, clear and honest.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open your kitchen dashboard and go to Public Page or Edit Photos.\n'
          '2. Check whether your hero image clearly represents {kitchen_name}.\n'
          '3. Replace any dark, blurry or confusing dish photos.\n'
          '4. Use natural light where possible.\n'
          '5. Avoid messy backgrounds that pull attention away from the food.\n'
          '6. Preview the public page after changing images.\n'
          '\n'
          'A simple test: if someone looks at your page for five seconds, can they understand what kind of food you '
          'make? If not, start with the hero image.\n'
          '\n'
          'This is available in your current plan.\n'
          '\n'
          'Open your public kitchen page:\n'
          '{public_kitchen_link}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: use Edit Photos to keep the public page fresh and replace weak images.\n'
          '- Business: connect better photos with QR posters and menu material, so offline customers see stronger food '
          'visuals when they scan.\n'
          '- Growth: use Marketing Coach and relevant Masterclass content to improve how you present food visually in '
          'posts and campaigns.\n'
          '- Pro: use BriteSight Photo Editor for image improvements such as crop, brightness and clarity before '
          'uploading. You can also use BriteSight Collage Builder when you want to show several dishes together.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 3,
  'required_plan': 'basic',
  'subject': 'This month in RiceMap24: make your food photos work harder',
  'title': 'Edit Photos: improve hero and dish images inside your kitchen page'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about your dish cards. In RiceMap24, each dish is more than a name '
          'and price. It is a small sales message that helps customers decide.\n'
          '\n'
          'Many customers may not know every dish, ingredient or regional name. A short explanation can make the '
          'difference between confusion and interest. This is especially important when selling Asian home-style food '
          'to customers from different backgrounds.\n'
          '\n'
          'Inside the app, review your dishes from the dish/menu area and then check how they appear on the public '
          'page. The goal is clear, useful and appetizing descriptions.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open your dish/menu editor.\n'
          '2. Choose three important dishes.\n'
          '3. Check whether the name is understandable for new customers.\n'
          '4. Add one short sentence about taste, ingredients or serving style.\n'
          '5. Mention whether the dish is mild, spicy, fresh, rich, comforting or good for sharing.\n'
          '6. Preview the public page after editing.\n'
          '\n'
          'A useful formula is: what it is + what it tastes like + how it is served.\n'
          '\n'
          'Example: “Chicken adobo with soy, vinegar and garlic. A classic Filipino comfort dish served with rice.”\n'
          '\n'
          'This is available in your current plan.\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: improve dish names and descriptions directly in your menu setup.\n'
          '- Business: use clearer dish text together with Customer List signals, so you can see which dishes people '
          'ask about and describe them better.\n'
          '- Growth: use Business Coach or Masterclass lessons about menu strategy to decide which dishes deserve more '
          'attention.\n'
          '- Pro: use BriteSight Design Studio or Pro Print Kit to turn your best dish descriptions into cleaner menu '
          'posters and shareable visual material.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 4,
  'required_plan': 'basic',
  'subject': 'This month in RiceMap24: improve your dish names and descriptions',
  'title': 'Dish and recipe setup: make dishes easier to choose'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about using your public kitchen link. Your RiceMap24 page gives you '
          'one simple place to send customers when you talk about your food.\n'
          '\n'
          'Instead of sending long messages with photos, prices, pickup information and payment details every time, '
          'you can point people to your kitchen page. This makes your communication cleaner and more professional.\n'
          '\n'
          'Inside RiceMap24, your public kitchen page can be used in social media posts, direct messages, local '
          'groups, QR material and customer follow-up.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open your public kitchen page.\n'
          '2. Copy the public kitchen link.\n'
          '3. Check that your current dishes and photos are updated.\n'
          '4. Write one simple post around one clear offer.\n'
          '5. Use the same link in Facebook, Instagram, WhatsApp or local community groups.\n'
          '6. Save the link somewhere easy so you can reuse it.\n'
          '\n'
          'Example post:\n'
          'Homemade food available for preorder this week. See menu and order details here: {public_kitchen_link}\n'
          '\n'
          'A clear link works best when the page behind it looks active and updated.\n'
          '\n'
          'This is available in your current plan.\n'
          '\n'
          'Open your public kitchen page:\n'
          '{public_kitchen_link}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: copy and share your public kitchen link whenever you promote your food.\n'
          '- Business: combine the link with Print & Promo and QR material, especially for pickup, local groups or '
          'small events.\n'
          '- Growth: use Marketing Coach to plan a simple weekly rhythm for Facebook, Instagram, WhatsApp and local '
          'sharing.\n'
          '- Pro: use BriteSight Design Studio, Collage Builder or Video Editor to create better posts around the same '
          'public kitchen link.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 5,
  'required_plan': 'basic',
  'subject': 'This month in RiceMap24: share your kitchen page more clearly',
  'title': 'Share your public kitchen link from RiceMap24'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about Customers & Results, especially Customer List. This part of '
          'RiceMap24 is for remembering who is interested in your food and what they usually ask for.\n'
          '\n'
          'Repeat customers are often easier to serve than completely new customers. If someone has ordered before, '
          'asked about a dish, reacted to a post or shown interest in a food drop, that information can help you plan '
          'better.\n'
          '\n'
          'Inside RiceMap24, Customer List can be used as a simple business memory. It helps you connect customer '
          'interest with your menu, future preorder plans and basic results.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open Customers & Results.\n'
          '2. Go to Customer List.\n'
          '3. Add a few customers or interested people from recent orders or messages.\n'
          '4. Note what they ordered, asked about or liked.\n'
          '5. Look for repeated interest in the same dishes.\n'
          '6. Use this when planning your next preorder or drop.\n'
          '\n'
          'This is not about collecting unnecessary data. It is about understanding what people come back for, so your '
          'next menu can be easier to plan.\n'
          '\n'
          '{plan_access_note}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: use the idea manually by noting repeat customers and popular dishes outside the app.\n'
          '- Business: use Customers & Results and Customer List as your practical memory for orders, interest and '
          'repeat buyers.\n'
          '- Growth: connect Customer List insights with Business Coach and Marketing Coach, so your next offer is '
          'based on actual customer signals.\n'
          '- Pro: use BriteSight tools to create targeted visuals for the dishes your customers already come back '
          'for.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 6,
  'required_plan': 'business',
  'subject': 'This month in RiceMap24: use Customer List to build repeat orders',
  'title': 'Customers & Results: use Customer List for repeat customers'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about Accounting & Insights inside Customers & Results. This is '
          'where your kitchen business becomes easier to understand with simple numbers.\n'
          '\n'
          'Even a small home kitchen needs basic visibility: income, expenses, customer activity and receipts. Without '
          'numbers, it is easy to feel busy without knowing whether the kitchen is actually moving in the right '
          'direction.\n'
          '\n'
          'Inside RiceMap24, Accounting & Insights is designed for simple tracking, not complicated accounting. You '
          'can connect income and expenses to customers where useful, and you can use the information to understand '
          'what works.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open Customers & Results.\n'
          '2. Go to Accounting & Insights.\n'
          '3. Add income after a sale or preorder round.\n'
          '4. Add important expenses such as ingredients, packaging or delivery-related costs.\n'
          '5. Connect entries to customers when relevant.\n'
          '6. Review the month and look for patterns.\n'
          '\n'
          'Useful questions to ask: Which dishes bring repeat interest? Which weeks are strongest? Are prices still '
          'reasonable after ingredients, packaging and time?\n'
          '\n'
          '{plan_access_note}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: start manually by writing down income, ingredient costs and which dishes are worth repeating.\n'
          '- Business: use Accounting & Insights inside Customers & Results to track income, expenses and receipts '
          'more professionally.\n'
          '- Growth: use Business Coach to turn your numbers into decisions about pricing, preorder size and repeat '
          'offers.\n'
          '- Pro: combine better numbers with BriteSight Design Studio and Pro Print Kit to promote your most '
          'profitable dishes more clearly.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 7,
  'required_plan': 'business',
  'subject': 'This month in RiceMap24: understand your kitchen numbers',
  'title': 'Customers & Results: use Accounting & Insights'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about using your kitchen page for preorder and drop planning. '
          'RiceMap24 is not meant to force you into being open all the time. A home kitchen can work better when '
          'customers know exactly what is available and when.\n'
          '\n'
          'A preorder or drop model can reduce stress. You choose the dishes, the number of portions, the order '
          'deadline and the pickup window. Then you use your public kitchen page as the clear place customers can '
          'check the menu and details.\n'
          '\n'
          'Inside the app, make sure your dish list, descriptions and public page support the offer you want to '
          'share.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Choose one or two dishes for a specific date.\n'
          '2. Update your public page so those dishes are easy to find.\n'
          '3. Write a clear order deadline.\n'
          '4. Write a clear pickup or delivery window.\n'
          '5. Share the public kitchen link with one simple message.\n'
          '6. If portions are limited, say so clearly.\n'
          '\n'
          'Example:\n'
          'Friday preorder: 20 portions available. Order by Thursday 18:00. Pickup Friday 16:00–18:00. Menu here: '
          '{public_kitchen_link}\n'
          '\n'
          'This is available in your current plan.\n'
          '\n'
          'Open your public kitchen page:\n'
          '{public_kitchen_link}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: use your public page and dish list to make the preorder offer clear.\n'
          '- Business: use Customer List and Accounting & Insights to understand which preorder ideas are most '
          'realistic.\n'
          '- Growth: use Marketing Coach to plan a simple campaign around each preorder or food drop.\n'
          '- Pro: use BriteSight Design Studio, Video Editor or Collage Builder to create stronger preorder visuals '
          'for social media.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 8,
  'required_plan': 'basic',
  'subject': 'This month in RiceMap24: make preorders easier to manage',
  'title': 'Preorder and drop planning from your kitchen page'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about Business Academy. This is the learning and growth area inside '
          'RiceMap24, built to help kitchen owners improve step by step.\n'
          '\n'
          'The point is not to read everything at once. The point is to use one piece of content and turn it into one '
          'practical change in your kitchen business. Depending on your plan, Business Academy may include starter '
          'guides, Business Coach, Marketing Coach and Masterclass content.\n'
          '\n'
          'Inside the app, Business Academy is connected to the same practical work you already do: kitchen page, '
          'photos, dishes, customer communication, local marketing and growth.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open Business Academy.\n'
          '2. Choose one guide, coach item or masterclass that fits your current situation.\n'
          '3. Write down one action from it.\n'
          '4. Apply that action to your kitchen page, menu, photos, sharing or customer follow-up.\n'
          '5. Check the result after one week.\n'
          '\n'
          'Example: if the lesson is about better food photos, update one dish photo. If it is about local growth, '
          'share your QR poster in one relevant place. If it is about menu strategy, improve one dish title or '
          'description.\n'
          '\n'
          '{plan_access_note}\n'
          '\n'
          'Open Business Academy:\n'
          '{business_academy_link}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: use the starter guides and apply one small improvement to your public page.\n'
          '- Business: combine starter business content with Customer List and Accounting & Insights, so learning '
          'becomes practical.\n'
          '- Growth: use Business Coach, Marketing Coach and Masterclass as a monthly development path for your '
          'kitchen.\n'
          '- Pro: connect the learning content with BriteSight creative tools, so strategy, marketing and visuals '
          'improve together.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 9,
  'required_plan': 'growth',
  'subject': 'This month in RiceMap24: use Business Academy inside the app',
  'title': 'Business Academy: use lessons, coach content and masterclasses'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about the menu and poster tools. Your public kitchen page is '
          'important, but sometimes you also need a shareable menu image, a poster, or a more visual way to present '
          'selected dishes.\n'
          '\n'
          'Inside RiceMap24, Tools can help you create practical promotional material based on your kitchen and '
          'dishes. This can be useful for social media, local groups, QR sharing, pickup areas or preorder '
          'announcements.\n'
          '\n'
          'The strongest menu material is usually simple. It should show the food clearly, highlight the dishes you '
          'most want to sell, and make it easy to reach your kitchen page.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open Tools.\n'
          '2. Choose Print & Promo or the available menu/poster tool for your plan.\n'
          '3. Select the dishes you want to promote most.\n'
          '4. Keep the layout easy to read on mobile.\n'
          '5. Include your QR code or public kitchen link.\n'
          '6. Use the finished material in one post, message or local setting.\n'
          '\n'
          'Think of the menu/poster as a doorway. It should not contain everything. It should make people want to open '
          'the full kitchen page.\n'
          '\n'
          '{plan_access_note}\n'
          '\n'
          'Open Print & Promo:\n'
          '{print_tools_link}\n'
          '\n'
          'Open your public kitchen page:\n'
          '{public_kitchen_link}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: use your public kitchen page as the main menu link, even if advanced print tools are locked.\n'
          '- Business: use Print & Promo for basic QR and menu material.\n'
          '- Growth: use Pro Print Kit-style menu/poster thinking together with Marketing Coach and Masterclass '
          'content to improve your promotional material.\n'
          '- Pro: use Pro Print Kit together with BriteSight Design Studio, Photo Editor and Collage Builder to create '
          'more professional menus, posters and campaign visuals.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 10,
  'required_plan': 'business',
  'subject': 'This month in RiceMap24: use menu and poster tools',
  'title': 'Tools: create clearer menus and posters'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about preparing your kitchen for busier periods. Weekends, holidays, '
          'local events, workplace lunches and community gatherings can create good opportunities, but only if your '
          'page and offer are clear before people need them.\n'
          '\n'
          'RiceMap24 can act as your preparation hub: public page, dishes, photos, QR material, customer signals and '
          'simple results all point toward the same goal — making it easier for people to understand and order from '
          '{kitchen_name}.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Choose one upcoming date, event or busy period.\n'
          '2. Decide what dish or menu you want to promote.\n'
          '3. Update your public page so the offer is easy to understand.\n'
          '4. Create or reuse QR/menu material if available.\n'
          '5. Share the public kitchen link early enough for people to plan.\n'
          '6. After the period, note what worked for next time.\n'
          '\n'
          'A clear offer is easier to say yes to. “Order by Thursday, pickup Friday” is often stronger than a general '
          'message saying food is available.\n'
          '\n'
          'This is available in your current plan.\n'
          '\n'
          'Open your public kitchen page:\n'
          '{public_kitchen_link}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: update your public page before a busy week so customers see the right dishes and pickup '
          'information.\n'
          '- Business: use Customer List, Accounting & Insights and Print & Promo to plan and promote the opportunity '
          'more clearly.\n'
          '- Growth: use Marketing Coach to prepare a small campaign before the busy period, instead of posting '
          'randomly at the last minute.\n'
          '- Pro: use BriteSight Video Editor, Design Studio or Pro Print Kit to create stronger material for events, '
          'holidays or workplace lunch offers.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 11,
  'required_plan': 'basic',
  'subject': 'This month in RiceMap24: prepare your kitchen for busier periods',
  'title': 'Dashboard planning: prepare for busy weeks and local opportunities'},
 {'audience': 'all',
  'body': 'Hi {owner_name},\n'
          '\n'
          'This month’s RiceMap24 Owner Update is about reviewing your kitchen setup and making one useful improvement '
          'before the next month.\n'
          '\n'
          'RiceMap24 works best when the page is not treated as finished forever. Food changes, photos improve, '
          'customer interest changes, and some dishes become clearer winners than others. A monthly review keeps the '
          'page active and more useful.\n'
          '\n'
          'Inside the app, look at the parts that matter most: public page, hero image, dish list, descriptions, '
          'customer signals and any available results.\n'
          '\n'
          'Try this in the app this month:\n'
          '1. Open your public kitchen page and check the first impression.\n'
          '2. Review your most important dishes.\n'
          '3. Remove, hide or improve anything that feels unclear.\n'
          '4. Update one old photo.\n'
          '5. Check whether prices and portion descriptions still make sense.\n'
          '6. Choose one dish, offer or preorder idea for next month.\n'
          '\n'
          'You do not need to rebuild everything. One improvement each month is enough to make the kitchen page '
          'stronger over time.\n'
          '\n'
          'This is available in your current plan.\n'
          '\n'
          'Open your public kitchen page:\n'
          '{public_kitchen_link}\n'
          '\n'
          'More you can do inside RiceMap24:\n'
          '- Basic: review your public page, photos and dish list before starting a new month.\n'
          '- Business: review Customer List and Accounting & Insights to see what actually worked.\n'
          '- Growth: use Business Coach, Marketing Coach and Masterclass to choose your next improvement area.\n'
          '- Pro: refresh your visual material with BriteSight Photo Editor, Design Studio, Collage Builder, Video '
          'Editor and Pro Print Kit so next month starts stronger.\n'
          '\n'
          'Open your RiceMap24 dashboard:\n'
          '{dashboard_link}\n'
          '\n'
          'This is an automated RiceMap24 owner update.\n'
          'Please do not reply to this email.',
  'month': 12,
  'required_plan': 'basic',
  'subject': 'This month in RiceMap24: review and improve your kitchen setup',
  'title': 'Results review: improve your page, menu and next offer'}]

def _owner_dashboard_link(listing: dict) -> str:
    token = str(listing.get("preview_token") or "").strip()
    if token:
        return f"/owner/{token}"
    slug = str(listing.get("slug") or "").strip()
    return f"/c/{slug}" if slug else "/"


def _owner_public_kitchen_link(listing: dict) -> str:
    slug = str(listing.get("slug") or "").strip()
    return f"/c/{slug}" if slug else _owner_dashboard_link(listing)


def _owner_dashboard_section_link(listing: dict, section: str) -> str:
    base = _owner_dashboard_link(listing)
    section = str(section or "").strip()
    return f"{base}#{section}" if section else base


def _render_owner_template(text: str, listing: dict) -> str:
    contact = listing.get("contact") or {}
    if not isinstance(contact, dict):
        contact = {}
    replacements = {
        "kitchen_name": str(listing.get("name") or "your kitchen"),
        "owner_name": str(contact.get("name") or listing.get("name") or "there"),
        "plan": str(listing.get("plan") or "basic"),
        "country": str(listing.get("country") or ""),
        "city": str(listing.get("city") or ""),
        "dashboard_link": _owner_dashboard_link(listing),
        "public_kitchen_link": _owner_public_kitchen_link(listing),
        "support_ticket_link": _owner_dashboard_section_link(listing, "support"),
        "business_academy_link": _owner_dashboard_section_link(listing, "business-academy"),
        "print_tools_link": _owner_dashboard_section_link(listing, "tools"),
        "pricing_link": "/pricing",
        "customer_no": str(listing.get("customer_no") or ""),
    }
    out = str(text or "")
    for k, v in replacements.items():
        out = out.replace("{" + k + "}", v)
    return out


def _owner_email(listing: dict) -> str:
    contact = listing.get("contact") or {}
    if isinstance(contact, dict):
        return str(contact.get("email") or "").strip()
    return ""


def _owner_template_by_key(key: str) -> Optional[dict]:
    kk = str(key or "").strip()
    for t in OWNER_EMAIL_TEMPLATES:
        if str(t.get("key") or "") == kk:
            return t
    return None


def _owner_email_opted_out(listing: dict, email_kind: str = "marketing") -> bool:
    """Return True if the owner has opted out of non-transactional product/tip emails.

    MVP note: preferences may later be controlled from the owner dashboard. For now we
    support several safe contact flags without requiring a schema change.
    """
    kind = str(email_kind or "marketing").lower()
    if kind in {"transactional", "billing", "support"}:
        return False
    contact = listing.get("contact") or {}
    if not isinstance(contact, dict):
        contact = {}
    for pref_key in ("email_updates", "monthly_owner_updates", "marketing_emails", "product_updates"):
        if pref_key in contact and contact.get(pref_key) is False:
            return True
        if str(contact.get(pref_key, "")).strip().lower() in {"0", "false", "no", "off", "disabled", "unsubscribed"}:
            return True
    if str(contact.get("email_opt_out") or "").strip().lower() in {"1", "true", "yes", "all", "marketing"}:
        return True
    return False


def _plan_rank(plan: str) -> int:
    return {"basic": 1, "business": 2, "growth": 3, "pro": 4}.get(str(plan or "basic").lower(), 1)


def _monthly_plan_access_note(listing: dict, theme: dict) -> str:
    plan = str((listing or {}).get("plan") or "basic").lower()
    required = str((theme or {}).get("required_plan") or "basic").lower()
    required_label = {"basic": "Basic", "business": "Business", "growth": "Growth", "pro": "Pro"}.get(required, required.title())
    plan_label = {"basic": "Basic", "business": "Business", "growth": "Growth", "pro": "Pro"}.get(plan, plan.title())
    title = str((theme or {}).get("title") or "this feature")
    if _plan_rank(plan) >= _plan_rank(required):
        return f"This is included in your current {plan_label} plan."
    manual = {
        2: "You can still use the same idea manually for now: share your public kitchen link clearly wherever customers already meet you.",
        6: "You can still use the same idea manually for now: keep a simple list of repeat customers and what they usually order.",
        7: "You can still use the same idea manually for now: write down income, key costs and repeat orders so you understand what is working.",
        9: "You can still use this month’s idea: choose one part of your kitchen page and improve it step by step.",
        10: "You can still use the same idea manually for now: create one clear menu image and share your kitchen link with it.",
    }.get(int((theme or {}).get("month") or 0), "You can still use the same idea manually for now.")
    return f"This feature is available from the {required_label} plan. {manual}\n\nWant access inside your dashboard? You can review your plan options here:\n{{pricing_link}}"


def _monthly_theme_for_listing(listing: dict, now: Optional[datetime] = None) -> dict:
    now = now or datetime.utcnow()
    month = int(now.strftime("%m"))
    theme = next((x for x in MONTHLY_OWNER_UPDATE_THEMES if int(x.get("month") or 0) == month), None)
    if not theme:
        theme = MONTHLY_OWNER_UPDATE_THEMES[0]
    theme = dict(theme)
    theme["body"] = str(theme.get("body") or "").replace("{plan_access_note}", _monthly_plan_access_note(listing, theme))
    return theme

def _ensure_owner_email_events_table() -> None:
    conn = connect()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS owner_email_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              listing_id INTEGER NOT NULL,
              event_key TEXT NOT NULL,
              template_key TEXT NOT NULL,
              notification_id INTEGER,
              status TEXT DEFAULT 'queued',
              created_at TEXT DEFAULT (datetime('now')),
              UNIQUE(listing_id, event_key)
            );
            CREATE INDEX IF NOT EXISTS idx_owner_email_events_listing ON owner_email_events(listing_id);
            CREATE INDEX IF NOT EXISTS idx_owner_email_events_event ON owner_email_events(event_key);
        """)
        conn.commit()
    finally:
        conn.close()


def _owner_email_event_exists(listing_id: int, event_key: str) -> bool:
    _ensure_owner_email_events_table()
    conn = connect()
    try:
        r = conn.execute(
            "SELECT id FROM owner_email_events WHERE listing_id=? AND event_key=? LIMIT 1",
            (int(listing_id), str(event_key or "")),
        ).fetchone()
        return bool(r)
    finally:
        conn.close()


def _record_owner_email_event(listing_id: int, event_key: str, template_key: str, notification_id: Optional[int], status: str = "queued") -> None:
    _ensure_owner_email_events_table()
    conn = connect()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO owner_email_events
                 (listing_id, event_key, template_key, notification_id, status)
               VALUES (?, ?, ?, ?, ?)""",
            (int(listing_id), str(event_key or "")[:120], str(template_key or "")[:80], int(notification_id) if notification_id else None, str(status or "queued")[:40]),
        )
        conn.commit()
    finally:
        conn.close()


def _queue_owner_template_once(listing: dict, template_key: str, event_key: Optional[str] = None, *, template_override: Optional[dict] = None, reason: str = "") -> dict:
    """Queue one owner email only once per listing/event. Returns {queued, skipped, reason}."""
    if not listing or not listing.get("id"):
        return {"queued": False, "skipped": True, "reason": "missing_listing"}
    lid = int(listing.get("id"))
    template_key = str(template_key or "").strip()
    event_key = str(event_key or template_key).strip()
    if _owner_email_event_exists(lid, event_key):
        return {"queued": False, "skipped": True, "reason": "already_queued", "event_key": event_key}
    email = _owner_email(listing)
    if not email:
        return {"queued": False, "skipped": True, "reason": "missing_email", "event_key": event_key}
    t = dict(template_override or _owner_template_by_key(template_key) or {})
    if not t:
        return {"queued": False, "skipped": True, "reason": "missing_template", "event_key": event_key}
    email_kind = str(t.get("email_kind") or t.get("category") or "marketing").lower()
    if _owner_email_opted_out(listing, email_kind):
        _record_owner_email_event(lid, event_key, template_key, None, "skipped_opt_out")
        return {"queued": False, "skipped": True, "reason": "opted_out", "event_key": event_key}
    item = queue_admin_notification(
        f"owner_{template_key}",
        recipient_type="owner",
        recipient_email=email,
        subject=_render_owner_template(str(t.get("subject") or ""), listing)[:240],
        body=_render_owner_template(str(t.get("body") or ""), listing),
        listing_id=lid,
        details={
            "template_key": template_key,
            "event_key": event_key,
            "source": "owner_email_automation",
            "email_kind": email_kind,
            "reason": reason or str(t.get("reason") or ""),
            "monthly_theme": t.get("title") or "",
        },
        status="queued",
    )
    _record_owner_email_event(lid, event_key, template_key, item.get("id"), "queued")
    return {"queued": True, "skipped": False, "event_key": event_key, "notification_id": item.get("id"), "reason": reason or str(t.get("reason") or "")}


def _parse_dt(value: str) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:19] if "T" in raw else raw[:19], fmt)
        except Exception:
            continue
    return None


def _listing_has_ready_content(listing: dict) -> bool:
    has_hero = bool(str(listing.get("hero_image") or "").strip())
    dishes = listing.get("dishes") or listing.get("menu") or []
    has_dishes = isinstance(dishes, list) and len(dishes) > 0
    return has_hero and has_dishes


def _generate_owner_email_automation_for_listing(listing: dict, now: Optional[datetime] = None) -> list[dict]:
    now = now or datetime.utcnow()
    if not listing or not listing.get("id"):
        return []
    published = int(listing.get("published") or 0) == 1
    created = _parse_dt(str(listing.get("created_at") or "")) or now
    age_days = max(0, int((now - created).total_seconds() // 86400))
    out: list[dict] = []
    candidates: list[dict] = []

    access_expires = str(listing.get("access_expires_at") or "").strip()
    exp = _parse_dt(access_expires)
    if exp:
        days_left = int((exp - now).total_seconds() // 86400)
        if 0 <= days_left <= 7:
            candidates.append({"priority": 10, "template_key": "trial_ending_owner", "event_key": f"trial_ending_owner_{access_expires[:10]}", "reason": "Trial/access expiry is 0–7 days away."})

    candidates.append({"priority": 20, "template_key": "welcome_new_owner", "event_key": "welcome_new_owner", "reason": "New owner registration / welcome email."})

    if age_days >= 1 and not published and not _listing_has_ready_content(listing):
        candidates.append({"priority": 30, "template_key": "complete_kitchen_page", "event_key": "complete_kitchen_page_day1", "reason": "Kitchen is not published and is missing hero image or dishes."})

    if not published and _listing_has_ready_content(listing):
        candidates.append({"priority": 40, "template_key": "ready_to_publish", "event_key": "ready_to_publish", "reason": "Kitchen has hero image and at least one dish, but is not published."})

    if published and age_days >= 3:
        candidates.append({"priority": 50, "template_key": "first_orders_tip", "event_key": "first_orders_tip_day3", "reason": "Published kitchen is ready for first-order promotion tips."})
    if published and age_days >= 7:
        candidates.append({"priority": 60, "template_key": "qr_poster_reminder", "event_key": "qr_poster_reminder_day7", "reason": "Published kitchen can benefit from QR/poster promotion."})

    plan = str(listing.get("plan") or "basic").lower()
    month_key = now.strftime("%Y-%m")
    if published and plan in {"growth", "pro"}:
        candidates.append({"priority": 70, "template_key": "new_content_available", "event_key": f"new_content_available_{month_key}", "reason": "Published Growth/Pro kitchen has Business Academy content available this month."})

    if published and str(listing.get("account_status") or "active").lower() in {"active", "trial"}:
        settings = get_admin_settings()
        monthly_day = int(settings.get("monthly_owner_update_day") or 2)
        monthly_day = max(1, min(28, monthly_day))
        if int(now.day) >= monthly_day:
            theme = _monthly_theme_for_listing(listing, now)
            candidates.append({
                "priority": 80,
                "template_key": "monthly_owner_update",
                "event_key": f"monthly_owner_update_{month_key}",
                "template_override": {
                    "key": "monthly_owner_update",
                    "name": "Monthly owner update",
                    "category": "news",
                    "email_kind": "marketing",
                    "subject": theme.get("subject") or "This month in RiceMap24",
                    "body": theme.get("body") or "",
                    "title": theme.get("title") or "Monthly Owner Update",
                },
                "reason": f"Monthly Owner Update: {theme.get('title') or 'app opportunity'}. Scheduled from day {monthly_day} of the calendar month; billing/content unlocks follow each owner’s subscription cycle.",
            })

    for c in sorted(candidates, key=lambda x: int(x.get("priority") or 999)):
        res = _queue_owner_template_once(listing, c.get("template_key"), c.get("event_key"), template_override=c.get("template_override"), reason=c.get("reason") or "")
        out.append(res)
        if res.get("queued"):
            break
    return out


def _listing_matches_comm_audience(listing: dict, audience: str) -> bool:
    audience = str(audience or "all").strip().lower()
    plan = str(listing.get("plan") or "basic").strip().lower()
    status = str(listing.get("account_status") or "active").strip().lower()
    published = int(listing.get("published") or 0) == 1
    data_dishes = listing.get("dishes") or listing.get("menu") or []
    if audience in ("all", "all_owners"):
        return True
    if audience == "active":
        return status == "active" and int(listing.get("plan_active") or 0) == 1
    if audience == "trial":
        return status == "trial" or str(listing.get("access_type") or "") == "trial"
    if audience == "not_ready":
        has_hero = bool(str(listing.get("hero_image") or "").strip())
        has_dishes = isinstance(data_dishes, list) and len(data_dishes) > 0
        return (not published) and (not has_hero or not has_dishes)
    if audience == "published":
        return published
    if audience == "unpublished":
        return not published
    if audience in {"basic", "business", "growth", "pro"}:
        return plan == audience
    if audience == "no_hero":
        return not str(listing.get("hero_image") or "").strip()
    if audience == "no_dishes":
        return not isinstance(data_dishes, list) or len(data_dishes) == 0
    if audience == "has_email":
        return bool(_owner_email(listing))
    return True


@app.get("/api/admin/communications/templates")
def admin_communication_templates(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return {"items": OWNER_EMAIL_TEMPLATES}


@app.post("/api/admin/communications/queue")
def admin_queue_owner_communication(request: Request, payload: dict = None, key: Optional[str] = None):
    _check_admin(key, request=request)
    p = payload or {}
    subject_tpl = str(p.get("subject") or "").strip()
    body_tpl = str(p.get("body") or "").strip()
    template_key = str(p.get("template_key") or "manual_owner_email").strip()[:80]
    audience = str(p.get("audience") or "all").strip().lower()
    listing_id_raw = p.get("listing_id")
    if not subject_tpl:
        raise HTTPException(status_code=400, detail="Missing subject")
    if not body_tpl:
        raise HTTPException(status_code=400, detail="Missing body")

    listings = admin_list(status="all")
    if listing_id_raw not in (None, "", 0, "0"):
        try:
            lid = int(listing_id_raw)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid listing_id")
        listings = [x for x in listings if int(x.get("id") or 0) == lid]
    else:
        listings = [x for x in listings if _listing_matches_comm_audience(x, audience)]

    queued = []
    skipped = []
    for listing in listings[:500]:
        email = _owner_email(listing)
        if not email:
            skipped.append({"listing_id": listing.get("id"), "name": listing.get("name"), "reason": "missing_email"})
            continue
        item = queue_admin_notification(
            f"owner_{template_key}",
            recipient_type="owner",
            recipient_email=email,
            subject=_render_owner_template(subject_tpl, listing)[:240],
            body=_render_owner_template(body_tpl, listing),
            listing_id=int(listing.get("id")),
            details={"template_key": template_key, "audience": audience, "source": "admin_communications"},
            status="queued",
        )
        queued.append(item)
    try:
        log_admin_activity(
            "owner_communication_queue",
            entity_type="admin_notification",
            title="Queued owner communication",
            details={"template_key": template_key, "audience": audience, "queued": len(queued), "skipped": len(skipped)},
        )
    except Exception:
        pass
    return {"ok": True, "queued": len(queued), "skipped": len(skipped), "items": queued[:50]}

@app.post("/api/admin/communications/generate-automatic")
def admin_generate_automatic_owner_emails(request: Request, payload: dict = None, key: Optional[str] = None):
    """Generate due owner emails from the onboarding/content rules. Idempotent: each event is queued once per kitchen."""
    _check_admin(key, request=request)
    p = payload or {}
    limit = max(1, min(int(p.get("limit") or 500), 1000))
    listings = admin_list(status="all")[:limit]
    results = []
    queued = 0
    skipped = 0
    for listing in listings:
        events = _generate_owner_email_automation_for_listing(listing)
        for ev in events:
            if not ev:
                continue
            if ev.get("queued"):
                queued += 1
            else:
                skipped += 1
        if events:
            results.append({
                "listing_id": listing.get("id"),
                "name": listing.get("name"),
                "events": events,
            })
    try:
        log_admin_activity(
            "owner_email_automation_generate",
            entity_type="admin_notification",
            title="Generated automatic owner emails",
            details={"queued": queued, "skipped": skipped, "listings_checked": len(listings)},
        )
    except Exception:
        pass
    return {"ok": True, "queued": queued, "skipped": skipped, "listings_checked": len(listings), "results": results[:100]}


@app.get("/api/admin/communications/monthly-themes")
def admin_owner_monthly_update_themes(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return {"items": MONTHLY_OWNER_UPDATE_THEMES}


@app.get("/api/admin/communications/automation-plan")
def admin_owner_email_automation_plan(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return {
        "items": [
            {"event": "welcome_new_owner", "template_key": "welcome_new_owner", "when": "Immediately after registration", "audience": "new owner"},
            {"event": "complete_kitchen_page_day1", "template_key": "complete_kitchen_page", "when": "Day 1+ if not published and missing hero image or dishes", "audience": "unfinished setup"},
            {"event": "ready_to_publish", "template_key": "ready_to_publish", "when": "When hero image and at least one dish exist, but page is still unpublished", "audience": "ready draft"},
            {"event": "kitchen_published", "template_key": "kitchen_published", "when": "Immediately when the owner publishes the kitchen", "audience": "published kitchen"},
            {"event": "first_orders_tip_day3", "template_key": "first_orders_tip", "when": "From day 3 after registration, if published", "audience": "published kitchen"},
            {"event": "qr_poster_reminder_day7", "template_key": "qr_poster_reminder", "when": "From day 7 after registration, if published", "audience": "published kitchen"},
            {"event": "monthly_owner_update_YYYY-MM", "template_key": "monthly_owner_update", "when": "Once per calendar month for active/trial published kitchens, from the configured calendar day (default day 2). This is separate from billing and paid content unlocks, which follow each owner’s subscription cycle.", "audience": "published active/trial"},
            {"event": "new_content_available_YYYY-MM", "template_key": "new_content_available", "when": "Once per calendar month for Growth/Pro published kitchens", "audience": "Growth/Pro"},
            {"event": "trial_ending_owner_DATE", "template_key": "trial_ending_owner", "when": "When trial/access expiry is 0–7 days away", "audience": "trial/access ending"},
        ]
    }


@app.get("/api/admin/discount-codes")
def admin_discount_codes(request: Request, key: Optional[str] = None, q: str = "", active: str = "all"):
    _check_admin(key, request=request)
    items = list_discount_codes(q=q, active=active)
    return {"items": items, "count": len(items)}


@app.post("/api/admin/discount-codes")
def admin_create_discount_code(payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    try:
        code = upsert_discount_code(payload or {})
        try:
            log_admin_activity("discount_code_create", entity_type="discount_code", entity_id=code.get("id"), title=code.get("code") or "Discount code", details={"code": code})
        except Exception:
            pass
        return {"ok": True, "code": code}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/admin/discount-codes/{code_id}")
def admin_update_discount_code(code_id: int, payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    try:
        code = upsert_discount_code(payload or {}, code_id=code_id)
        try:
            log_admin_activity("discount_code_update", entity_type="discount_code", entity_id=code_id, title=code.get("code") or f"Discount code {code_id}", details={"patch_keys": list((payload or {}).keys())})
        except Exception:
            pass
        return {"ok": True, "code": code}
    except KeyError:
        raise HTTPException(status_code=404, detail="Discount code not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@app.get("/api/admin/discount-codes/health")
def admin_discount_codes_health(request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    return {"ok": True, "module": "discount_codes", "version": "step7.70"}

@app.get("/api/admin/discount-codes/")
def admin_discount_codes_slash(request: Request, key: Optional[str] = None, q: str = "", active: str = "all"):
    return admin_discount_codes(key=key, q=q, active=active)

@app.post("/api/admin/discount-codes/")
def admin_create_discount_code_slash(payload: dict, request: Request, key: Optional[str] = None):
    return admin_create_discount_code(payload=payload, key=key)


@app.post("/api/admin/discount-codes/{code_id}/toggle")
@app.post("/api/admin/discount-codes/{code_id}/active")
def admin_set_discount_code_active(code_id: int, payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    try:
        active = bool((payload or {}).get("active"))
        code = set_discount_code_active(code_id, active)
        try:
            log_admin_activity("discount_code_toggle", entity_type="discount_code", entity_id=code_id, title=code.get("code") or f"Discount code {code_id}", details={"active": active})
        except Exception:
            pass
        return {"ok": True, "code": code}
    except KeyError:
        raise HTTPException(status_code=404, detail="Discount code not found")


@app.post("/api/admin/activity/log-view-as-kitchen")
def admin_log_view_as_kitchen(payload: dict, request: Request, key: Optional[str] = None):
    _check_admin(key, request=request)
    p = payload or {}
    listing_id = int(p.get("listing_id") or 0)
    item = get_by_id(listing_id) if listing_id else None
    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")
    log_admin_activity(
        "view_as_kitchen",
        entity_type="listing",
        entity_id=listing_id,
        listing_id=listing_id,
        customer_no=item.get("customer_no") or "",
        title=item.get("name") or f"Listing {listing_id}",
        details={"slug": item.get("slug"), "preview_token_used": bool(item.get("preview_token"))},
    )
    return {"ok": True}


@app.post("/api/uploads")
async def upload_image(
    draft_id: int = Form(...),
    kind: str = Form(...),
    dish_index: Optional[int] = Form(None),
    file: UploadFile = File(...),
):
    """
    Upload images for a draft/listing. Stores files under /uploads/<draft_id>/.
    kind: hero | signature | dish
    dish_index: required for kind=dish
    Returns: {"url": "/uploads/<id>/<filename>"}.
    """
    item = get_by_id(draft_id)
    if not item:
        raise HTTPException(status_code=404, detail="Draft/listing not found")

    # basic type allow-list
    allowed = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    ext = allowed.get(file.content_type or "")
    if not ext:
        # fallback: infer from filename
        name = (file.filename or "").lower()
        if name.endswith(".jpg") or name.endswith(".jpeg"):
            ext = ".jpg"
        elif name.endswith(".png"):
            ext = ".png"
        elif name.endswith(".webp"):
            ext = ".webp"
        else:
            raise HTTPException(status_code=400, detail="Unsupported image type")

    if kind == "dish" and dish_index is None:
        raise HTTPException(status_code=400, detail="dish_index required for kind=dish")

    safe_kind = "".join([c for c in kind.lower() if c.isalnum() or c in ("-", "_")])[:24] or "img"
    di = f"-{int(dish_index)}" if dish_index is not None else ""
    fname = f"{safe_kind}{di}-{uuid.uuid4().hex}{ext}"

    out_dir = (UPLOADS_DIR / str(draft_id)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / fname

    # Limit upload size so a single request cannot fill the server disk.
    max_bytes = int(runtime_config.upload_max_mb) * 1024 * 1024
    written = 0
    with out_path.open("wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                try:
                    out_path.unlink(missing_ok=True)
                except Exception:
                    pass
                raise HTTPException(status_code=413, detail=f"Image is too large. Maximum size is {runtime_config.upload_max_mb} MB")
            f.write(chunk)

    return {"url": f"/uploads/{draft_id}/{fname}"}




# --- Masterclass library -----------------------------------------------------

_MASTERCLASS_INDEX: dict[str, dict] = {}
_MASTERCLASS_ORDER: list[str] = []
_MASTERCLASS_FIRST_MONTH_IDS: set[str] = set()
_MASTERCLASS_BASIC_IDS: set[str] = set()


def _month_last_day(year: int, month: int) -> int:
    if month == 12:
        nxt = datetime(year + 1, 1, 1)
    else:
        nxt = datetime(year, month + 1, 1)
    return (nxt - timedelta(days=1)).day


def _add_months_keep_day(dt: datetime, months: int) -> datetime:
    year = dt.year + ((dt.month - 1 + months) // 12)
    month = ((dt.month - 1 + months) % 12) + 1
    day = min(dt.day, _month_last_day(year, month))
    return dt.replace(year=year, month=month, day=day)


def _parse_dt_safe(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        raw = raw.replace('Z', '+00:00')
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is not None:
            return dt.astimezone().replace(tzinfo=None)
        return dt
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    return None


def _full_months_since(start_dt: datetime | None, now_dt: datetime | None = None) -> int:
    if not start_dt:
        return 0
    now_dt = now_dt or datetime.utcnow()
    if now_dt < start_dt:
        return 0
    months = (now_dt.year - start_dt.year) * 12 + (now_dt.month - start_dt.month)
    while months > 0 and _add_months_keep_day(start_dt, months) > now_dt:
        months -= 1
    return max(0, months)


def _subscription_schedule_start(listing: dict | None) -> datetime:
    """Return the subscription start used for drip/unlock schedules.

    Monthly content must be based on when the subscription became active, not on
    when the kitchen/listing was originally created. If old/demo records do not
    have activated_at yet, treat the subscription as starting now so future
    Masterclasses stay locked until the next subscription month.
    """
    return _parse_dt_safe((listing or {}).get('activated_at')) or datetime.utcnow()


def _masterclass_sort_key(code: str):
    s = str(code or '').strip()
    m = re.match(r'^(\d+)(?:[-_ ]?([A-Za-z]))?$', s)
    if m:
        n = int(m.group(1))
        letter = (m.group(2) or '').upper()
        rank = (ord(letter) - 64) if letter else 99
        return (n, rank, s.lower())
    m2 = re.match(r'^(\d+)', s)
    if m2:
        return (int(m2.group(1)), 99, s.lower())
    return (9999, 999, s.lower())


def _masterclass_code_from_stem(stem: str) -> str:
    s = str(stem or '')
    s = re.sub(r'^masterclass_', '', s, flags=re.IGNORECASE)
    first = s.split('_', 1)[0]
    if re.match(r'^\d{2}-[A-Za-z]$', first):
        return first.upper()
    m = re.match(r'^(\d{2})', s)
    if m:
        return m.group(1)
    return stem


def _clean_masterclass_title(title: str) -> str:
    t = str(title or '').strip()
    t = re.sub(r'^Masterclass\s*(?:\d+|\d+[A-Za-z-]*)?\s*[—–-]\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\(For Home Kitchens\)\s*$', '', t, flags=re.IGNORECASE)
    return t.strip() or str(title or '').strip()


def _clean_masterclass_md(md: str) -> str:
    text = (md or '').replace('\r\n', '\n').replace('\r', '\n')
    out: list[str] = []
    skip_visual_notes = False

    def _is_visual_heading(s: str) -> bool:
        core = re.sub(r'^#{1,6}\s*', '', s).strip().lower()
        return (
            core.startswith('image & illustration notes')
            or core.startswith('hero image')
            or core.startswith('illustration ')
            or core.startswith('diagram ')
            or core.startswith('visual notes')
        )

    for raw in text.split('\n'):
        line = raw.rstrip()
        s = line.strip()
        if skip_visual_notes:
            if s.startswith('#') and not _is_visual_heading(s):
                skip_visual_notes = False
            else:
                continue
        if s.startswith('#') and _is_visual_heading(s):
            skip_visual_notes = True
            continue
        if re.match(r'^!\[[^\]]*\]\([^\)]*\)$', s):
            continue
        if re.match(r'^!\[[^\]]*\]\[[^\]]*\]$', s):
            continue
        if re.match(r'^[-*_]{3,}$', s):
            continue
        if 'hero image' in s.lower() and ('![' in s or s.lower().startswith('image:') or s.lower().startswith('picture:')):
            continue
        out.append(line)
    cleaned = '\n'.join(out)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned + ('\n' if cleaned else '')


def _load_masterclass_index() -> None:
    global _MASTERCLASS_INDEX, _MASTERCLASS_ORDER, _MASTERCLASS_FIRST_MONTH_IDS, _MASTERCLASS_BASIC_IDS

    files = sorted([p for p in MASTERCLASS_DIR.rglob('*.md') if p.is_file() and '__MACOSX' not in str(p)])
    idx: dict[str, dict] = {}

    for p in files:
        rid = p.stem
        code = _masterclass_code_from_stem(rid)
        md_raw = p.read_text(encoding='utf-8', errors='replace')
        title = rid
        for line in md_raw.split('\n'):
            if line.startswith('# '):
                title = line[2:].strip()
                break
        cleaned_md = _clean_masterclass_md(md_raw)
        teaser = ''
        raw_lines = [l.strip() for l in cleaned_md.split('\n')]
        try:
            i0 = next(i for i, l in enumerate(raw_lines) if l.startswith('# '))
        except StopIteration:
            i0 = 0
        for j in range(i0 + 1, min(i0 + 12, len(raw_lines))):
            if raw_lines[j] and not raw_lines[j].startswith('![') and not raw_lines[j].startswith('**What you will learn') and not raw_lines[j].startswith('**Who this is for'):
                teaser = raw_lines[j]
                break
        image_stem = rid.replace('masterclass_', '', 1)
        image_url = ''
        for ext in ('.jpg', '.jpeg', '.png', '.webp'):
            image_name = image_stem + ext
            if (MASTERCLASS_IMAGES_DIR / image_name).exists():
                image_url = f'/masterclass_images/{image_name}'
                break
        idx[rid] = {
            'id': rid,
            'code': code,
            'title': _clean_masterclass_title(title),
            'teaser': teaser,
            'path': str(p),
            'image_url': image_url,
        }

    order = sorted(idx.keys(), key=lambda k: _masterclass_sort_key(idx[k].get('code') or k))
    _MASTERCLASS_INDEX = idx
    _MASTERCLASS_ORDER = order
    _MASTERCLASS_FIRST_MONTH_IDS = {rid for rid in order if str(idx[rid].get('code')).upper() in {'01-A','01-B','01-C','01-D','01-E','01-F'}}
    _MASTERCLASS_BASIC_IDS = {rid for rid in order if str(idx[rid].get('code')).upper() in {'01-A','01-D'}}


def _ensure_masterclass_loaded():
    global _MASTERCLASS_ORDER
    try:
        if not _MASTERCLASS_ORDER:
            _load_masterclass_index()
    except Exception:
        pass


def _masterclass_allowed_by_plan(plan: str, masterclass_id: str, listing: dict | None = None) -> bool:
    """Hard access matrix for Masterclass.

    Basic: selected starter lessons only (01-A and 01-D).
    Business: first-month starter set only (01-A through 01-F).
    Growth/Pro: handled by monthly unlock schedule in _masterclass_access().
    """
    plan = _normalize_plan(plan)
    meta = _MASTERCLASS_INDEX.get(masterclass_id) or {}
    code = str(meta.get('code') or '').upper().strip()
    if plan == 'basic':
        return code in {'01-A', '01-D'}
    if plan == 'business':
        return code in {'01-A', '01-B', '01-C', '01-D', '01-E', '01-F'}
    return False


def _masterclass_access(listing: dict, masterclass_id: str) -> dict:
    _ensure_masterclass_loaded()
    plan = _normalize_plan(str((listing or {}).get('plan') or 'basic'))
    start_dt = _subscription_schedule_start(listing)
    months_since = _full_months_since(start_dt)

    visible_title = True
    can_open = False
    tier = plan
    unlock_at = None

    if plan in ('growth', 'pro') or _feature_override_active(listing, 'masterclass'):
        unlocked_count = min(len(_MASTERCLASS_ORDER), 6 + months_since)
        unlocked_ids = set(_MASTERCLASS_ORDER[:unlocked_count])
        can_open = masterclass_id in unlocked_ids
        if not can_open:
            try:
                idx = _MASTERCLASS_ORDER.index(masterclass_id)
                extra_idx = max(0, idx - 5)
                unlock_at = _add_months_keep_day(start_dt, extra_idx) if start_dt else None
            except Exception:
                unlock_at = None
    else:
        # Explicit non-Growth matrix. This prevents Basic from inheriting
        # the Business first-month set through shared starter-content logic.
        can_open = _masterclass_allowed_by_plan(plan, masterclass_id, listing)

    return {
        'tier': tier,
        'can_open': bool(can_open),
        'visible_title': bool(visible_title),
        'unlock_at': unlock_at.isoformat(sep=' ') if unlock_at else None,
        'months_since': months_since,
    }


@app.get('/api/owner/{token}/masterclass')
def owner_list_masterclass(token: str):
    _ensure_masterclass_loaded()
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail='Not found')

    plan = _normalize_plan(str(listing.get('plan') or 'basic'))
    start_dt = _subscription_schedule_start(listing)
    months_since = _full_months_since(start_dt)

    items = []
    for rid in _MASTERCLASS_ORDER:
        meta = _MASTERCLASS_INDEX.get(rid) or {}
        acc = _masterclass_access(listing, rid)
        items.append({
            'id': rid,
            'code': meta.get('code') or rid,
            'title': meta.get('title') if acc.get('visible_title') else '',
            'teaser': meta.get('teaser') if acc.get('can_open') else '',
            'image_url': meta.get('image_url') or '',
            'locked': not bool(acc.get('can_open')),
            'visible_title': bool(acc.get('visible_title')),
            'unlock_at': acc.get('unlock_at'),
        })

    current_masterclass = None
    if _MASTERCLASS_ORDER:
        try:
            if plan in ('growth', 'pro') or _feature_override_active(listing, 'masterclass'):
                # Month 1 opens only the starter set (01-A to 01-F).
                # Month 2 opens the first post-starter Masterclass, but only after
                # the next subscription-month boundary has actually been reached.
                idx = 0 if months_since <= 0 else min(len(_MASTERCLASS_ORDER) - 1, 5 + months_since)
                rid = _MASTERCLASS_ORDER[idx]
                meta = _MASTERCLASS_INDEX.get(rid) or {}
                acc = _masterclass_access(listing, rid)
                if acc.get('can_open'):
                    current_masterclass = {
                        'id': rid,
                        'code': meta.get('code') or rid,
                        'title': meta.get('title') or rid,
                        'image_url': meta.get('image_url') or '',
                        'subscription_month': int(months_since or 0) + 1,
                        'starter_set': bool(months_since <= 0),
                        'can_open': True,
                    }
        except Exception:
            current_masterclass = None

    return {
        'plan': plan,
        'counts': {
            'total': len(_MASTERCLASS_ORDER),
            'first_month': len(_MASTERCLASS_FIRST_MONTH_IDS),
            'basic_open': len(_MASTERCLASS_BASIC_IDS),
        },
        'current_masterclass': current_masterclass,
        'subscription_month': int(months_since or 0) + 1,
        'items': items,
    }


@app.get('/api/owner/{token}/masterclass/{masterclass_id}')
def owner_get_masterclass(token: str, masterclass_id: str):
    _ensure_masterclass_loaded()
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail='Not found')
    meta = _MASTERCLASS_INDEX.get(masterclass_id)
    if not meta:
        raise HTTPException(status_code=404, detail='Masterclass not found')
    acc = _masterclass_access(listing, masterclass_id)
    if not acc.get('can_open'):
        raise HTTPException(status_code=403, detail='Upgrade or wait for unlock')
    md = Path(meta['path']).read_text(encoding='utf-8', errors='replace')
    md = _clean_masterclass_md(md)
    md_lines = md.splitlines()
    if md_lines and md_lines[0].startswith('# '):
        md = '\n'.join(md_lines[1:]).lstrip('\n')
    html = _md_to_html(md)
    return {
        'id': masterclass_id,
        'code': meta.get('code') or masterclass_id,
        'title': meta.get('title') or masterclass_id,
        'plan': _normalize_plan(str(listing.get('plan') or 'basic')),
        'image_url': meta.get('image_url') or '',
        'html': html,
    }


# --- Marketing Coach library -----------------------------------------------

_MARKETING_COACH_INDEX: dict[str, dict] = {}
_MARKETING_COACH_ORDER: list[str] = []
_MARKETING_COACH_FIRST_MONTH_IDS: set[str] = set()
_MARKETING_COACH_BASIC_IDS: set[str] = set()


def _marketing_coach_sort_key(code: str):
    return _masterclass_sort_key(code)


def _marketing_coach_code_from_stem(stem: str) -> str:
    s = str(stem or '')
    s = re.sub(r'^marketing_coach_', '', s, flags=re.IGNORECASE)
    m = re.match(r'^(\d{2})[-_ ]?([A-Za-z])$', s)
    if m:
        return f"{m.group(1)}-{m.group(2).upper()}"
    m = re.match(r'^(\d{2})', s)
    if m:
        return m.group(1)
    return stem


def _clean_marketing_coach_title(title: str) -> str:
    t = str(title or '').strip()
    t = re.sub(r'^Focus:\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'^Marketing Coach\s*[—–-]\s*Month\s*[\dA-Za-z-]+\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'^Marketing Coach\s*[—–-]\s*', '', t, flags=re.IGNORECASE)
    return t.strip(' -–—') or str(title or '').strip()


def _clean_marketing_coach_md(md: str) -> str:
    return _clean_masterclass_md(md)


def _load_marketing_coach_index() -> None:
    global _MARKETING_COACH_INDEX, _MARKETING_COACH_ORDER, _MARKETING_COACH_FIRST_MONTH_IDS, _MARKETING_COACH_BASIC_IDS

    files = sorted([p for p in MARKETING_COACH_DIR.rglob('*.md') if p.is_file() and '__MACOSX' not in str(p)])
    idx: dict[str, dict] = {}

    for p in files:
        rid = p.stem
        code = _marketing_coach_code_from_stem(rid)
        md_raw = p.read_text(encoding='utf-8', errors='replace')
        h1 = ''
        h2 = ''
        for line in md_raw.split('\n'):
            if not h1 and line.startswith('# '):
                h1 = line[2:].strip()
                continue
            if not h2 and line.startswith('## '):
                h2 = line[3:].strip()
                break
        title = h2 or h1 or rid
        cleaned_md = _clean_marketing_coach_md(md_raw)
        teaser = ''
        raw_lines = [l.strip() for l in cleaned_md.split('\n')]
        for j, line in enumerate(raw_lines[:16]):
            if line and not line.startswith('#') and not line.startswith('!['):
                teaser = line
                break
        image_url = ''
        for ext in ('.jpg', '.jpeg', '.png', '.webp'):
            image_name = f"{code}{ext}"
            if (MARKETING_COACH_IMAGES_DIR / image_name).exists():
                image_url = f'/marketing_coach_images/{image_name}'
                break
        idx[rid] = {
            'id': rid,
            'code': code,
            'title': _clean_marketing_coach_title(title),
            'teaser': teaser,
            'path': str(p),
            'image_url': image_url,
        }

    order = sorted(idx.keys(), key=lambda k: _marketing_coach_sort_key(idx[k].get('code') or k))
    _MARKETING_COACH_INDEX = idx
    _MARKETING_COACH_ORDER = order
    _MARKETING_COACH_FIRST_MONTH_IDS = {rid for rid in order if str(idx[rid].get('code')).upper() in {'01-A','01-B'}}
    _MARKETING_COACH_BASIC_IDS = {rid for rid in order if str(idx[rid].get('code')).upper() in {'01-B'}}


def _ensure_marketing_coach_loaded():
    global _MARKETING_COACH_ORDER
    try:
        if not _MARKETING_COACH_ORDER:
            _load_marketing_coach_index()
    except Exception:
        pass


def _marketing_coach_access(listing: dict, item_id: str) -> dict:
    _ensure_marketing_coach_loaded()
    plan = _normalize_plan(str((listing or {}).get('plan') or 'basic'))
    start_dt = _subscription_schedule_start(listing)
    months_since = _full_months_since(start_dt)

    visible_title = True
    can_open = False
    tier = plan
    unlock_at = None

    if plan in ('growth', 'pro') or _feature_override_active(listing, 'marketing_coach'):
        unlocked_count = min(len(_MARKETING_COACH_ORDER), 2 + months_since)
        unlocked_ids = set(_MARKETING_COACH_ORDER[:unlocked_count])
        can_open = item_id in unlocked_ids
        if not can_open:
            try:
                idx = _MARKETING_COACH_ORDER.index(item_id)
                extra_idx = max(0, idx - 1)
                unlock_at = _add_months_keep_day(start_dt, extra_idx) if start_dt else None
            except Exception:
                unlock_at = None
    else:
        # Basic and Business may preview Marketing Coach topics as locked teasers,
        # but Marketing Coach content itself requires Growth or Pro.
        can_open = False
        unlock_at = None

    return {
        'tier': tier,
        'can_open': bool(can_open),
        'visible_title': bool(visible_title),
        'unlock_at': unlock_at.isoformat(sep=' ') if unlock_at else None,
        'months_since': months_since,
    }


@app.get('/api/owner/{token}/marketing-coach')
def owner_list_marketing_coach(token: str):
    _ensure_marketing_coach_loaded()
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail='Not found')
    plan = _normalize_plan(str(listing.get('plan') or 'basic'))
    is_preview_plan = plan in ('basic', 'business') and not _feature_override_active(listing, 'marketing_coach')
    # Basic and Business should see only a focused preview: this month's starter
    # Marketing Coach items plus next month as an upgrade teaser. Do not expose
    # the full future schedule to lower tiers.
    visible_order = _MARKETING_COACH_ORDER[:3] if is_preview_plan else _MARKETING_COACH_ORDER

    items = []
    for rid in visible_order:
        meta = _MARKETING_COACH_INDEX.get(rid) or {}
        acc = _marketing_coach_access(listing, rid)
        items.append({
            'id': rid,
            'code': meta.get('code') or rid,
            'title': meta.get('title') if acc.get('visible_title') else '',
            'teaser': meta.get('teaser') if acc.get('can_open') else '',
            'image_url': meta.get('image_url') or '',
            'locked': not bool(acc.get('can_open')),
            'visible_title': bool(acc.get('visible_title')),
            'unlock_at': acc.get('unlock_at'),
        })
    return {
        'plan': plan,
        'counts': {
            'total': len(_MARKETING_COACH_ORDER),
            'first_month': len(_MARKETING_COACH_FIRST_MONTH_IDS),
            'basic_open': len(_MARKETING_COACH_BASIC_IDS),
        },
        'items': items,
    }


@app.get('/api/owner/{token}/marketing-coach/{item_id}')
def owner_get_marketing_coach(token: str, item_id: str):
    _ensure_marketing_coach_loaded()
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail='Not found')
    meta = _MARKETING_COACH_INDEX.get(item_id)
    if not meta:
        raise HTTPException(status_code=404, detail='Marketing Coach not found')
    acc = _marketing_coach_access(listing, item_id)
    if not acc.get('can_open'):
        raise HTTPException(status_code=403, detail='Upgrade or wait for unlock')
    md = Path(meta['path']).read_text(encoding='utf-8', errors='replace')
    md = _clean_marketing_coach_md(md)
    md_lines = md.splitlines()
    while md_lines and (md_lines[0].startswith('# ') or md_lines[0].startswith('## ')):
        md_lines = md_lines[1:]
    md = '\n'.join(md_lines).lstrip('\n')
    html = _md_to_html(md)
    return {
        'id': item_id,
        'code': meta.get('code') or item_id,
        'title': meta.get('title') or item_id,
        'plan': _normalize_plan(str(listing.get('plan') or 'basic')),
        'image_url': meta.get('image_url') or '',
        'html': html,
    }




# --- Business Coach library -----------------------------------------------

_BUSINESS_COACH_INDEX: dict[str, dict] = {}
_BUSINESS_COACH_ORDER: list[str] = []
_BUSINESS_COACH_BASIC_IDS: set[str] = set()


def _business_coach_sort_key(code: str):
    return _masterclass_sort_key(code)


def _business_coach_code_from_stem(stem: str) -> str:
    s = str(stem or '')
    s = re.sub(r'^business[ _-]?coach[ _-]?#?', '', s, flags=re.IGNORECASE).strip()
    m = re.match(r'^(\d{2})[-_ ]?([A-Za-z])(?=$|[_ -])', s)
    if m:
        return f"{m.group(1)}-{m.group(2).upper()}"
    m = re.match(r'^(\d{2})', s)
    if m:
        return m.group(1)
    return stem


def _clean_business_coach_title(title: str) -> str:
    t = str(title or '').strip()
    t = re.sub(r'^Business Coach\s*#?\s*[\dA-Za-z-]+\s*[—–-]\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'^Business Coach\s*[—–-]\s*', '', t, flags=re.IGNORECASE)
    return t.strip(' -–—') or str(title or '').strip()


def _clean_business_coach_md(md: str) -> str:
    return _clean_masterclass_md(md)


def _slugify_loose(s: str) -> str:
    s = str(s or '').lower()
    s = s.replace('’', "'").replace('“', '"').replace('”', '"')
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s


def _load_business_coach_index() -> None:
    global _BUSINESS_COACH_INDEX, _BUSINESS_COACH_ORDER, _BUSINESS_COACH_BASIC_IDS

    files = sorted([p for p in BUSINESS_COACH_DIR.rglob('*.md') if p.is_file() and '__MACOSX' not in str(p)])
    idx: dict[str, dict] = {}

    image_files = [p for p in BUSINESS_COACH_IMAGES_DIR.rglob('*') if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'}]
    image_map: dict[str, str] = {}
    image_map_exact: dict[str, str] = {}
    for p in image_files:
        image_map[_slugify_loose(p.stem)] = p.name
        m = re.match(r'^(\d{2})[-_ ]?([A-Za-z])(?=$|[_ -])', p.stem)
        if m:
            image_map_exact[f"{m.group(1)}-{m.group(2).upper()}"] = p.name

    for p in files:
        rid = p.stem
        code = _business_coach_code_from_stem(rid)
        md_raw = p.read_text(encoding='utf-8', errors='replace')
        h1 = ''
        h2 = ''
        for line in md_raw.split('\n'):
            if not h1 and line.startswith('# '):
                h1 = line[2:].strip()
                continue
            if not h2 and line.startswith('## '):
                h2 = line[3:].strip()
                break
        # Use the main H1 as the visible Business Coach title.
        # The H2 acts as a subtitle / teaser, not the primary card title.
        title = h1 or h2 or rid
        subtitle = h2 or ''
        cleaned_md = _clean_business_coach_md(md_raw)
        teaser = subtitle.strip()
        raw_lines = [l.strip() for l in cleaned_md.split('\n')]
        if not teaser:
            for j, line in enumerate(raw_lines[:16]):
                if line and not line.startswith('#') and not line.startswith('!['):
                    teaser = line
                    break
        image_url = ''
        image_name = image_map_exact.get(str(code).upper())
        if not image_name:
            wanted = _slugify_loose(f"{code}_{title}")
            best = None
            best_score = -1
            for norm, name in image_map.items():
                score = 0
                if norm.startswith(_slugify_loose(str(code))):
                    score += 100
                common = len(os.path.commonprefix([norm, wanted]))
                score += common
                if score > best_score:
                    best = name
                    best_score = score
            image_name = best or ''
        if image_name:
            image_url = f'/business_coach_images/{image_name}'
        idx[rid] = {
            'id': rid,
            'code': code,
            'title': _clean_business_coach_title(title),
            'teaser': teaser,
            'path': str(p),
            'image_url': image_url,
        }

    order = sorted(idx.keys(), key=lambda k: _business_coach_sort_key(idx[k].get('code') or k))
    _BUSINESS_COACH_INDEX = idx
    _BUSINESS_COACH_ORDER = order
    _BUSINESS_COACH_BASIC_IDS = {rid for rid in order if str(idx[rid].get('code')).upper() in {'01-A','01-B'}}


def _ensure_business_coach_loaded():
    global _BUSINESS_COACH_ORDER
    try:
        if not _BUSINESS_COACH_ORDER:
            _load_business_coach_index()
    except Exception:
        pass


def _business_coach_unlock_at(start_dt, item_id: str):
    if not start_dt:
        return None
    meta = _BUSINESS_COACH_INDEX.get(item_id) or {}
    code = str(meta.get('code') or '')
    m = re.match(r'^(\d{2})[-_ ]?([A-Za-z])(?=$|[_ -])', code)
    if not m:
        return None
    month_num = int(m.group(1))
    letter = (m.group(2) or 'A').upper()

    # Business Coach has starter content in month 1:
    # 01-A and 01-B are available immediately.
    if month_num == 1:
        return start_dt

    # From month 2 onward, each numbered cycle unlocks in that month:
    # A on the subscription day, B on day 15 of that same cycle.
    dt = _add_months_keep_day(start_dt, max(0, month_num - 1))
    if letter == 'B':
        dt = dt + timedelta(days=14)
    return dt


def _business_coach_access(listing: dict, item_id: str) -> dict:
    _ensure_business_coach_loaded()
    plan = _normalize_plan(str((listing or {}).get('plan') or 'basic'))
    raw_start_dt = _parse_dt_safe((listing or {}).get('activated_at')) or _parse_dt_safe((listing or {}).get('created_at'))
    now_dt = datetime.utcnow()

    visible_title = True
    tier = plan
    can_open = False

    # Robust fallback: if older/demo listings do not have a usable subscription
    # date yet, treat the first Business Coach cycle as having started now so the
    # first item is immediately usable instead of everything appearing locked.
    start_dt = raw_start_dt or now_dt
    unlock_at = _business_coach_unlock_at(start_dt, item_id)

    # Starter Content is open for all plans.
    if item_id in _BUSINESS_COACH_BASIC_IDS:
        can_open = True
        unlock_at = None
    elif plan == 'basic' and not _feature_override_active(listing, 'business_coach'):
        can_open = False
        unlock_at = None
    else:
        can_open = bool(unlock_at and unlock_at <= now_dt)

    return {
        'tier': tier,
        'can_open': bool(can_open),
        'visible_title': bool(visible_title),
        'unlock_at': unlock_at.isoformat(sep=' ') if unlock_at else None,
    }


@app.get('/api/owner/{token}/business-coach')
def owner_list_business_coach(token: str):
    _ensure_business_coach_loaded()
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail='Not found')
    items = []
    for rid in _BUSINESS_COACH_ORDER:
        meta = _BUSINESS_COACH_INDEX.get(rid) or {}
        acc = _business_coach_access(listing, rid)
        items.append({
            'id': rid,
            'code': meta.get('code') or rid,
            'title': meta.get('title') if acc.get('visible_title') else '',
            'teaser': meta.get('teaser') if acc.get('can_open') else '',
            'image_url': meta.get('image_url') or '',
            'locked': not bool(acc.get('can_open')),
            'visible_title': bool(acc.get('visible_title')),
            'unlock_at': acc.get('unlock_at'),
        })
    return {
        'plan': _normalize_plan(str(listing.get('plan') or 'basic')),
        'counts': {
            'total': len(_BUSINESS_COACH_ORDER),
            'basic_open': len(_BUSINESS_COACH_BASIC_IDS),
        },
        'items': items,
    }


@app.get('/api/owner/{token}/business-coach/{item_id}')
def owner_get_business_coach(token: str, item_id: str):
    _ensure_business_coach_loaded()
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail='Not found')
    meta = _BUSINESS_COACH_INDEX.get(item_id)
    if not meta:
        raise HTTPException(status_code=404, detail='Business Coach not found')
    acc = _business_coach_access(listing, item_id)
    if not acc.get('can_open'):
        raise HTTPException(status_code=403, detail='Upgrade or wait for unlock')
    md = Path(meta['path']).read_text(encoding='utf-8', errors='replace')
    md = _clean_business_coach_md(md)
    md_lines = md.splitlines()
    while md_lines and (md_lines[0].startswith('# ') or md_lines[0].startswith('## ')):
        md_lines = md_lines[1:]
    md = '\n'.join(md_lines).lstrip('\n')
    html = _md_to_html(md)
    return {
        'id': item_id,
        'code': meta.get('code') or item_id,
        'title': meta.get('title') or item_id,
        'plan': _normalize_plan(str(listing.get('plan') or 'basic')),
        'image_url': meta.get('image_url') or '',
        'html': html,
    }


# --- Recipes (owner) --------------------------------------------------------

def _ensure_recipes_loaded():
    """Fail-safe: if the recipe index didn't load at import time (e.g. folder missing),
    try loading again at request time so the UI doesn't show an empty library."""
    global _RECIPES_ORDER, _RECIPES_INDEX
    try:
        if not _RECIPES_ORDER:
            _load_recipes_index()
    except Exception:
        # Keep it silent; endpoints will return empty results or 404 as appropriate.
        pass

@app.get("/api/owner/{token}/recipes")
def owner_list_recipes(token: str):
    _ensure_recipes_loaded()
    # Accept both preview_token and slug (owner dashboards commonly use slug)
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Not found")
    plan = str(listing.get('plan') or 'basic')
    items = []
    for rid in _RECIPES_ORDER:
        meta = _RECIPES_INDEX.get(rid) or {}
        acc = _recipe_access(plan, rid)
        locked = not bool(acc.get('can_open'))
        items.append({
            'id': rid,
            'title': meta.get('title') or rid,
            'teaser': meta.get('teaser') or '',
            'tags': meta.get('tags') or {},
            'locked': locked,
            'strategy_unlocked': bool(acc.get('show_strategy')),
        })

    return {
        'plan': _normalize_plan(plan),
        'counts': {
            'total': len(_RECIPES_ORDER),
            'trial': len(_TRIAL_IDS),
            'standard_strategy': len(_STANDARD_STRATEGY_IDS),
        },
        'items': items,
    }


@app.get("/api/owner/{token}/recipes/{recipe_id}")
def owner_get_recipe(token: str, recipe_id: str):
    _ensure_recipes_loaded()
    # Accept both preview_token and slug
    listing = get_by_preview_token(token) or get_by_slug(token)
    if not listing:
        raise HTTPException(status_code=404, detail="Not found")

    plan = str(listing.get('plan') or 'basic')
    meta = _RECIPES_INDEX.get(recipe_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Recipe not found")

    acc = _recipe_access(plan, recipe_id)
    if not acc.get('can_open'):
        raise HTTPException(status_code=403, detail="Upgrade required")

    md = Path(meta['path']).read_text(encoding='utf-8', errors='replace')
    md = _clean_recipe_md(md)
    recipe_md, strategy_md = _split_strategy(md)

    # Compute related suggestions early so we can keep Strategy and Combos consistent.
    rel = _related_recipe_ids(recipe_id)

    # If the file doesn't include a Strategy Layer, generate one so the tab never looks empty.
    if not (strategy_md or '').strip():
        strategy_md = _generate_strategy_md_from_related(meta, recipe_md, recipe_id, rel)

    show_strategy = bool(acc.get('show_strategy'))
    if not show_strategy:
        # Replace strategy with a friendly upgrade prompt
        strategy_md = "## Strategy Layer\n\n> Locked on your plan. Upgrade to **Growth** to unlock full strategy for every recipe.\n"

    

    return {
        'id': recipe_id,
        'title': meta.get('title') or recipe_id,
        'tags': meta.get('tags') or {},
        'plan': _normalize_plan(plan),
        'show_strategy': show_strategy,
        'html': {
            'recipe': _md_to_html(recipe_md),
            'strategy': _md_to_html(strategy_md) if strategy_md else '',
        },
        'related': {
            'addons': [ _RECIPES_INDEX[r] for r in rel.get('addons', []) if r in _RECIPES_INDEX ],
            'similar': [ _RECIPES_INDEX[r] for r in rel.get('similar', []) if r in _RECIPES_INDEX ],
            'generic_addons': rel.get('generic_addons', []) or [],
        }
    }


@app.get("/api/debug/recipes")
def debug_recipes():
    """Small debug endpoint to verify that recipes are loaded."""
    _ensure_recipes_loaded()
    return {
        "total": len(_RECIPES_ORDER or []),
        "trial": len(_TRIAL_IDS or []),
        "standard_strategy": len(_STANDARD_STRATEGY_IDS or []),
        "dir": str(RECIPES_DIR),
    }



# --- Static web (single-process MVP) ---
if WEB_PUBLIC.exists():
    # serve uploaded images (local MVP)
    app.mount("/uploads", NoCacheStaticFiles(directory=str(UPLOADS_DIR), html=False), name="uploads")
    app.mount("/", NoCacheStaticFiles(directory=str(WEB_PUBLIC), html=True), name="web")


@app.exception_handler(404)
async def spa_fallback(request: Request, exc):
    """Return index.html for frontend routes (so /c/slug works on refresh)."""
    path = request.url.path

    # If it's an API path, keep normal 404
    if path.startswith("/api") or path.startswith("/health"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    # If it's a static asset request, keep 404
    if "." in Path(path).name:
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))

    return JSONResponse(status_code=404, content={"detail": "Web not built"})


if __name__ == "__main__":
    import uvicorn

    port = runtime_config.port
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=runtime_config.is_development)
