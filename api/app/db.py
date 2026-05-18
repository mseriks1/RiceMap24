from __future__ import annotations

import json
import math
import sqlite3
import re
import secrets
import hashlib
import hmac
import time
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
from .config import runtime_config

DB_ENGINE = runtime_config.database_engine
DB_URL = runtime_config.database_url
DB_PATH = Path(runtime_config.database_path).resolve() if runtime_config.database_path else (BASE_DIR / ".." / ".." / "ricemap24.sqlite3").resolve()
_SQLITE_PRAGMAS_READY = False

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # psycopg is only required when DATABASE_URL is PostgreSQL
    psycopg = None
    dict_row = None


def _pg_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    return value


class PgRow(dict):
    """Small sqlite3.Row-compatible dict row for PostgreSQL results."""
    def __init__(self, mapping=None, **kwargs):
        mapping = dict(mapping or {}, **kwargs)
        super().__init__({k: _pg_value(v) for k, v in mapping.items()})

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)

    def keys(self):
        return super().keys()


class PgCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return PgRow(row)
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [PgRow(r) if isinstance(r, dict) else r for r in rows]


class PgConnection:
    """Minimal sqlite-like connection wrapper around psycopg.

    The existing RiceMap24 data layer was written with sqlite3's API. This wrapper
    keeps that API stable while allowing staging/production to use PostgreSQL via
    DATABASE_URL. It intentionally does not add application features.
    """
    def __init__(self, conn):
        self._conn = conn

    def close(self):
        return self._conn.close()

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def execute(self, sql: str, params: Iterable[Any] | None = None):
        translated = _pg_translate_sql(sql)
        lowered = translated.strip().lower()
        if lowered.startswith("pragma table_info"):
            table = _pg_extract_pragma_table(sql)
            try:
                rows = _pg_table_info(self._conn, table)
                return StaticCursor(rows)
            except Exception:
                # PostgreSQL marks the whole transaction as failed after any SQL error.
                # SQLite code in _migrate() intentionally catches/ignores some migration
                # errors, so the wrapper must reset the transaction before continuing.
                self._conn.rollback()
                raise
        returning_id = _pg_should_return_id(translated)
        if returning_id:
            translated = translated.rstrip().rstrip(';') + " RETURNING id"
        cur = self._conn.cursor()
        try:
            cur.execute(translated, tuple(params or ()))
            wrapped = PgCursor(cur)
            if returning_id:
                try:
                    row = cur.fetchone()
                    if row:
                        wrapped.lastrowid = row.get('id') if isinstance(row, dict) else row[0]
                except Exception:
                    wrapped.lastrowid = None
            return wrapped
        except Exception:
            self._conn.rollback()
            raise

    def executemany(self, sql: str, seq_of_params):
        translated = _pg_translate_sql(sql)
        cur = self._conn.cursor()
        try:
            cur.executemany(translated, seq_of_params)
            return PgCursor(cur)
        except Exception:
            self._conn.rollback()
            raise

    def executescript(self, script: str):
        for stmt in _split_sql_script(script):
            if stmt.strip():
                self.execute(stmt)
        return StaticCursor([])


class StaticCursor:
    def __init__(self, rows):
        self._rows = [PgRow(r) if isinstance(r, dict) else r for r in rows]
        self.lastrowid = None

    def fetchone(self):
        if not self._rows:
            return None
        return self._rows.pop(0)

    def fetchall(self):
        rows = self._rows
        self._rows = []
        return rows


def _split_sql_script(script: str) -> List[str]:
    # The schema scripts in this project do not contain semicolons inside strings.
    return [part.strip() for part in script.split(';') if part.strip()]


def _pg_extract_pragma_table(sql: str) -> str:
    m = re.search(r"PRAGMA\s+table_info\(([^)]+)\)", sql, re.I)
    return (m.group(1).strip().strip('"') if m else '')


def _pg_table_info(conn, table: str):
    if not table:
        return []
    cur = conn.cursor()
    cur.execute(
        """
        SELECT column_name AS name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    rows = cur.fetchall()
    return rows or []


def _pg_should_return_id(sql: str) -> bool:
    s = sql.strip()
    low = s.lower()
    if not low.startswith('insert into'):
        return False
    if ' returning ' in low or ' on conflict ' in low:
        return False
    m = re.match(r"insert\s+into\s+([a-zA-Z_][a-zA-Z0-9_]*)", s, re.I)
    if not m:
        return False
    table = m.group(1).lower()
    return table not in {'admin_settings'}


def _pg_translate_sql(sql: str) -> str:
    out = sql
    out = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY", out, flags=re.I)
    out = re.sub(r"datetime\('now'\)", "CURRENT_TIMESTAMP", out, flags=re.I)
    out = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", out, flags=re.I)
    # Convert SQLite's INSERT OR IGNORE pattern to PostgreSQL conflict-safe insert.
    if re.search(r"^\s*INSERT\s+INTO\s+admin_settings", out, re.I) and "ON CONFLICT" not in out.upper():
        out = out.rstrip().rstrip(';') + " ON CONFLICT (key) DO NOTHING"
    # psycopg uses %s parameters, sqlite uses ?. The existing SQL does not use literal question marks.
    out = out.replace('?', '%s')
    return out



DEFAULT_ADMIN_SETTINGS = {
    "public_signups_enabled": "true",
    "new_kitchen_approval_required": "true",
    "default_trial_days": "14",
    "billing_grace_days": "3",
    "hide_unpaid_kitchens_automatically": "true",
    "support_tickets_enabled": "true",
    "referral_system_enabled": "true",
    "email_notifications_enabled": "true",
    "email_delivery_enabled": "false",  # false = safe queue/manual mode until domain/provider is ready
    "notify_new_tickets": "true",
    "notify_admin_replies": "true",
    "notify_trial_expiry": "true",
    "notify_overdue_payment": "true",
    "admin_notification_email": "admin@ricemap24.local",
    "email_provider": "manual",  # manual | smtp | sendgrid | postmark
    "email_from_name": "RiceMap24",
    "email_from_email": "no-reply@ricemap24.com",
    "email_reply_to": "no-reply@ricemap24.com",
    "email_dns_verified": "false",
    "smtp_host": "",
    "smtp_port": "587",
    "smtp_username": "",
    "smtp_password_set": "false",
    "sendgrid_api_key_set": "false",
    "postmark_server_token_set": "false",
    "monthly_owner_update_day": "2",
}

BOOL_ADMIN_SETTINGS = {"public_signups_enabled", "new_kitchen_approval_required", "hide_unpaid_kitchens_automatically", "support_tickets_enabled", "referral_system_enabled", "email_notifications_enabled", "email_delivery_enabled", "email_dns_verified", "notify_new_tickets", "notify_admin_replies", "notify_trial_expiry", "notify_overdue_payment", "smtp_password_set", "sendgrid_api_key_set", "postmark_server_token_set"}
INT_ADMIN_SETTINGS = {"default_trial_days", "billing_grace_days", "smtp_port", "monthly_owner_update_day"}


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS listings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_no TEXT UNIQUE,                  -- stable internal actor/customer number, e.g. RM24-000123
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  area TEXT,
  city TEXT,
  country TEXT,
  postcode TEXT,
  cuisines TEXT,         -- json array
  badges TEXT,           -- json array
  from_price INTEGER,
  currency TEXT,
  hero_image TEXT,

  -- demo / marketplace visibility
  is_demo INTEGER NOT NULL DEFAULT 0,
  listing_type TEXT NOT NULL DEFAULT 'real', -- real | demo
  accepts_orders INTEGER NOT NULL DEFAULT 1,
  show_in_actor_marketing INTEGER NOT NULL DEFAULT 1,
  show_in_customer_marketplace INTEGER NOT NULL DEFAULT 1,

  -- geo
  lat REAL,
  lng REAL,

  -- publishing / billing meta
  published INTEGER NOT NULL DEFAULT 0,              -- 1 = visible in portal
  plan TEXT DEFAULT 'basic',                         -- basic | business | growth | pro
  billing TEXT DEFAULT 'monthly',                    -- monthly | yearly
  plan_active INTEGER NOT NULL DEFAULT 1,            -- 1 = active subscription/access (manual admin in MVP)
  account_status TEXT NOT NULL DEFAULT 'active',        -- active | trial | past_due | cancelled | paused | archived | deleted_by_request
  preview_token TEXT,                                -- shareable preview (draft)
  pending_activation INTEGER NOT NULL DEFAULT 0,      -- 1 = requested to go live, waiting for admin
  requested_at TEXT,
  activated_at TEXT,

  -- admin CRM / manual billing (MVP)
  admin_note TEXT DEFAULT '',
  paid_status TEXT DEFAULT 'unpaid',                  -- unpaid | paid
  paid_until TEXT,
  last_payment_at TEXT,

  -- stripe (subscriptions)
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  stripe_checkout_session_id TEXT,
  stripe_status TEXT,
  stripe_price_id TEXT,
  stripe_current_period_end TEXT,
  stripe_last_event_at TEXT,

  data_json TEXT NOT NULL,    -- full listing json (includes menu etc.)
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);


CREATE TABLE IF NOT EXISTS app_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT,
  display_name TEXT DEFAULT '',
  role TEXT NOT NULL DEFAULT 'owner', -- owner | admin
  listing_id INTEGER,
  active INTEGER NOT NULL DEFAULT 1,
  email_verified INTEGER NOT NULL DEFAULT 0,
  last_login_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email);
CREATE INDEX IF NOT EXISTS idx_app_users_listing ON app_users(listing_id);
CREATE INDEX IF NOT EXISTS idx_app_users_role ON app_users(role);

CREATE TABLE IF NOT EXISTS app_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_token_hash TEXT UNIQUE NOT NULL,
  user_id INTEGER NOT NULL,
  role TEXT NOT NULL DEFAULT 'owner',
  ip TEXT DEFAULT '',
  user_agent TEXT DEFAULT '',
  expires_at TEXT NOT NULL,
  revoked_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_app_sessions_user ON app_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_app_sessions_expires ON app_sessions(expires_at);

CREATE TABLE IF NOT EXISTS login_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT DEFAULT '',
  ip TEXT DEFAULT '',
  success INTEGER NOT NULL DEFAULT 0,
  reason TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip);
CREATE INDEX IF NOT EXISTS idx_login_attempts_created ON login_attempts(created_at);

CREATE TABLE IF NOT EXISTS app_error_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL DEFAULT 'error',
  source TEXT NOT NULL DEFAULT 'backend',
  path TEXT DEFAULT '',
  method TEXT DEFAULT '',
  status_code INTEGER,
  message TEXT DEFAULT '',
  traceback TEXT DEFAULT '',
  request_id TEXT DEFAULT '',
  ip TEXT DEFAULT '',
  user_agent TEXT DEFAULT '',
  details_json TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_app_error_log_created ON app_error_log(created_at);
CREATE INDEX IF NOT EXISTS idx_app_error_log_level ON app_error_log(level);
CREATE INDEX IF NOT EXISTS idx_app_error_log_path ON app_error_log(path);

CREATE TABLE IF NOT EXISTS admin_settings (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS admin_activity_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor TEXT DEFAULT 'admin',
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id INTEGER,
  listing_id INTEGER,
  customer_no TEXT,
  title TEXT,
  details_json TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_admin_activity_created ON admin_activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_activity_listing ON admin_activity_log(listing_id);
CREATE INDEX IF NOT EXISTS idx_admin_activity_action ON admin_activity_log(action);


CREATE TABLE IF NOT EXISTS stripe_webhook_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT,
  event_type TEXT NOT NULL,
  listing_id INTEGER,
  subscription_id TEXT,
  customer_id TEXT,
  status TEXT NOT NULL DEFAULT 'processed', -- received | processed | ignored | error | simulated
  source TEXT DEFAULT 'webhook', -- webhook | admin_simulation
  message TEXT DEFAULT '',
  details_json TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_stripe_events_created ON stripe_webhook_events(created_at);
CREATE INDEX IF NOT EXISTS idx_stripe_events_type ON stripe_webhook_events(event_type);
CREATE INDEX IF NOT EXISTS idx_stripe_events_listing ON stripe_webhook_events(listing_id);

CREATE TABLE IF NOT EXISTS discount_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  description TEXT DEFAULT '',
  discount_type TEXT NOT NULL DEFAULT 'percent', -- percent | amount
  percent_off REAL,
  amount_off REAL,
  currency TEXT,
  applies_to_plan TEXT DEFAULT 'all',
  billing TEXT DEFAULT 'all',
  max_redemptions INTEGER,
  redemption_count INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1,
  starts_at TEXT,
  ends_at TEXT,
  internal_note TEXT DEFAULT '',
  builder_stage TEXT DEFAULT 'new_request',
  builder_recommended_plan TEXT DEFAULT '',
  builder_payment_status TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_discount_codes_code ON discount_codes(code);
CREATE INDEX IF NOT EXISTS idx_discount_codes_active ON discount_codes(active);

CREATE TABLE IF NOT EXISTS geocache (
  query_key TEXT PRIMARY KEY,
  display_name TEXT,
  lat REAL,
  lng REAL,
  provider TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id INTEGER NOT NULL,
  customer_no TEXT,   -- e.g. C-0001 (unique per listing)
  org_no TEXT,        -- optional organization number
  name TEXT NOT NULL,
  phone TEXT,
  email TEXT,
  tags TEXT,          -- json array
  notes TEXT,
  last_contacted_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_customers_listing ON customers(listing_id);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
-- NOTE: idx_customers_no_unique is created in _migrate() after ensuring the column exists.


CREATE TABLE IF NOT EXISTS accounting_transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id INTEGER NOT NULL,
  tx_date TEXT NOT NULL,             -- YYYY-MM-DD
  tx_type TEXT NOT NULL,             -- income | expense
  customer_id INTEGER,               -- optional link to customers.id (income)
  dish_name TEXT,                    -- optional dish/product (income)
  qty INTEGER DEFAULT 1,             -- optional quantity (income), default 1
  items_json TEXT,                   -- optional line items (json array)
  category TEXT,
  amount REAL NOT NULL,
  currency TEXT,
  note TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_acc_listing ON accounting_transactions(listing_id);
CREATE INDEX IF NOT EXISTS idx_acc_date ON accounting_transactions(tx_date);
-- NOTE: idx_acc_customer is created in _migrate() after ensuring the column exists.


CREATE TABLE IF NOT EXISTS receipts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id INTEGER NOT NULL,
  transaction_id INTEGER,            -- optional link to accounting_transactions.id
  receipt_no TEXT NOT NULL,          -- e.g. R-2026-0001
  public_token TEXT UNIQUE NOT NULL, -- shareable link token
  doc_type TEXT NOT NULL DEFAULT 'receipt',   -- receipt | invoice
  issue_date TEXT NOT NULL,          -- YYYY-MM-DD
  due_date TEXT,                     -- YYYY-MM-DD (invoice)
  paid INTEGER NOT NULL DEFAULT 1,   -- 1 = paid (receipt)
  paid_date TEXT,                    -- YYYY-MM-DD
  payment_method TEXT,               -- cash | vipps | card | bank | other

  buyer_name TEXT,
  buyer_org_no TEXT,
  buyer_email TEXT,
  buyer_phone TEXT,
  buyer_ref TEXT,

  description TEXT,
  items_json TEXT,
  amount REAL NOT NULL,
  currency TEXT,
  note TEXT,

  status TEXT NOT NULL DEFAULT 'issued',
  replaces_receipt_id INTEGER,

  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_receipts_listing ON receipts(listing_id);
CREATE INDEX IF NOT EXISTS idx_receipts_issue_date ON receipts(issue_date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_receipts_no_unique ON receipts(listing_id, receipt_no);
CREATE INDEX IF NOT EXISTS idx_receipts_tx ON receipts(transaction_id);


CREATE INDEX IF NOT EXISTS idx_listings_city ON listings(city);
CREATE INDEX IF NOT EXISTS idx_listings_postcode ON listings(postcode);
CREATE INDEX IF NOT EXISTS idx_listings_published ON listings(published);
CREATE INDEX IF NOT EXISTS idx_listings_preview_token ON listings(preview_token);
CREATE INDEX IF NOT EXISTS idx_listings_pending_activation ON listings(pending_activation);
CREATE INDEX IF NOT EXISTS idx_listings_latlng ON listings(lat,lng);
CREATE INDEX IF NOT EXISTS idx_geocache_updated ON geocache(updated_at);

-- Track partner / supplier clicks from Owner Dashboard (lightweight analytics)
CREATE TABLE IF NOT EXISTS supplier_clicks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id INTEGER NOT NULL,
  region TEXT,
  supplier_id TEXT,
  supplier_name TEXT,
  url TEXT,
  ip TEXT,
  user_agent TEXT,
  referer TEXT,
  meta_json TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_supplier_clicks_listing ON supplier_clicks(listing_id);
CREATE INDEX IF NOT EXISTS idx_supplier_clicks_created ON supplier_clicks(created_at);


-- Support tickets (MVP)
CREATE TABLE IF NOT EXISTS support_tickets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id INTEGER NOT NULL,
  subject TEXT NOT NULL,
  category TEXT DEFAULT 'general',
  status TEXT NOT NULL DEFAULT 'open',
  priority TEXT NOT NULL DEFAULT 'normal',
  created_by TEXT DEFAULT 'owner',
  internal_note TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_support_tickets_listing ON support_tickets(listing_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_support_tickets_updated ON support_tickets(updated_at);

CREATE TABLE IF NOT EXISTS support_ticket_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_id INTEGER NOT NULL,
  sender TEXT NOT NULL DEFAULT 'owner',
  body TEXT NOT NULL,
  is_internal INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_support_ticket_messages_ticket ON support_ticket_messages(ticket_id);

"""



def _ticket_row_to_dict(row: sqlite3.Row, include_messages: bool = False) -> Dict[str, Any]:
    item = {
        "id": int(row["id"]),
        "listing_id": int(row["listing_id"]),
        "subject": row["subject"],
        "category": row["category"],
        "status": row["status"],
        "priority": row["priority"],
        "created_by": row["created_by"],
        "internal_note": row["internal_note"] if "internal_note" in row.keys() else "",
        "builder_stage": row["builder_stage"] if "builder_stage" in row.keys() else "new_request",
        "builder_recommended_plan": row["builder_recommended_plan"] if "builder_recommended_plan" in row.keys() else "",
        "builder_payment_status": row["builder_payment_status"] if "builder_payment_status" in row.keys() else "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if include_messages:
        item["messages"] = []
    return item


def create_support_ticket(listing_id: int, subject: str, body: str, category: str = "general", created_by: str = "owner") -> Dict[str, Any]:
    subj = (subject or "").strip()[:180]
    msg = (body or "").strip()
    if not subj:
        raise ValueError("Subject is required")
    if not msg:
        raise ValueError("Message is required")
    conn = connect()
    try:
        row = conn.execute("SELECT id FROM listings WHERE id=?", (int(listing_id),)).fetchone()
        if not row:
            raise KeyError("listing not found")
        cur = conn.execute(
            """
            INSERT INTO support_tickets (listing_id, subject, category, status, priority, created_by)
            VALUES (?, ?, ?, 'open', 'normal', ?)
            """,
            (int(listing_id), subj, (category or "general")[:60], (created_by or "owner")[:30]),
        )
        tid = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO support_ticket_messages (ticket_id, sender, body, is_internal) VALUES (?, ?, ?, 0)",
            (tid, (created_by or "owner")[:30], msg),
        )
        conn.commit()
        return get_support_ticket(tid) or {"id": tid}
    finally:
        conn.close()


def list_support_tickets(listing_id: Optional[int] = None, status: str = "all") -> List[Dict[str, Any]]:
    refresh_billing_visibility()
    conn = connect()
    try:
        where: List[str] = []
        params: List[Any] = []
        if listing_id is not None:
            where.append("t.listing_id=?")
            params.append(int(listing_id))
        if status and status != "all":
            where.append("t.status=?")
            params.append(status)
        sql = """
            SELECT t.*, l.name AS listing_name, l.slug AS listing_slug, l.plan AS listing_plan, l.customer_no AS listing_customer_no
            FROM support_tickets t
            LEFT JOIN listings l ON l.id=t.listing_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY CASE t.status WHEN 'open' THEN 0 WHEN 'pending' THEN 1 WHEN 'closed' THEN 3 ELSE 2 END, t.updated_at DESC LIMIT 500"
        rows = conn.execute(sql, params).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = _ticket_row_to_dict(r)
            d["listing_name"] = r["listing_name"]
            d["listing_slug"] = r["listing_slug"]
            d["listing_plan"] = r["listing_plan"]
            d["listing_customer_no"] = r["listing_customer_no"] or listing_customer_no(int(r["listing_id"]))
            out.append(d)
        return out
    finally:
        conn.close()


def get_support_ticket(ticket_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute(
            """
            SELECT t.*, l.name AS listing_name, l.slug AS listing_slug, l.plan AS listing_plan, l.customer_no AS listing_customer_no
            FROM support_tickets t
            LEFT JOIN listings l ON l.id=t.listing_id
            WHERE t.id=?
            """,
            (int(ticket_id),),
        ).fetchone()
        if not row:
            return None
        d = _ticket_row_to_dict(row, include_messages=True)
        d["listing_name"] = row["listing_name"]
        d["listing_slug"] = row["listing_slug"]
        d["listing_plan"] = row["listing_plan"]
        d["listing_customer_no"] = row["listing_customer_no"] or listing_customer_no(int(row["listing_id"]))
        msgs = conn.execute(
            "SELECT id, ticket_id, sender, body, is_internal, created_at FROM support_ticket_messages WHERE ticket_id=? ORDER BY id ASC",
            (int(ticket_id),),
        ).fetchall()
        d["messages"] = [
            {"id": int(m["id"]), "ticket_id": int(m["ticket_id"]), "sender": m["sender"], "body": m["body"], "is_internal": int(m["is_internal"]), "created_at": m["created_at"]}
            for m in msgs
        ]
        return d
    finally:
        conn.close()


def add_support_ticket_message(ticket_id: int, sender: str, body: str, is_internal: int = 0) -> Dict[str, Any]:
    msg = (body or "").strip()
    if not msg:
        raise ValueError("Message is required")
    conn = connect()
    try:
        row = conn.execute("SELECT id FROM support_tickets WHERE id=?", (int(ticket_id),)).fetchone()
        if not row:
            raise KeyError("ticket not found")
        conn.execute(
            "INSERT INTO support_ticket_messages (ticket_id, sender, body, is_internal) VALUES (?, ?, ?, ?)",
            (int(ticket_id), (sender or "admin")[:30], msg, 1 if is_internal else 0),
        )
        new_status = "pending" if (sender or "") == "admin" and not is_internal else "open"
        conn.execute("UPDATE support_tickets SET status=?, updated_at=datetime('now') WHERE id=?", (new_status, int(ticket_id)))
        conn.commit()
        return get_support_ticket(int(ticket_id)) or {"id": int(ticket_id)}
    finally:
        conn.close()


def update_support_ticket(ticket_id: int, status: Optional[str] = None, priority: Optional[str] = None, internal_note: Optional[str] = None, builder_stage: Optional[str] = None, builder_recommended_plan: Optional[str] = None, builder_payment_status: Optional[str] = None) -> Dict[str, Any]:
    allowed_status = {"open", "pending", "closed"}
    allowed_priority = {"low", "normal", "high"}
    allowed_builder_stages = {"new_request", "reviewed", "recommendation_sent", "payment_pending", "paid", "session_1_booked", "in_progress", "strategy_delivered", "follow_up_completed", "closed"}
    allowed_builder_payments = {"", "not_sent", "offer_sent", "payment_pending", "paid", "payment_plan", "cancelled"}
    sets: List[str] = []
    params: List[Any] = []
    if status in allowed_status:
        sets.append("status=?")
        params.append(status)
    if priority in allowed_priority:
        sets.append("priority=?")
        params.append(priority)
    if internal_note is not None:
        sets.append("internal_note=?")
        params.append(internal_note)
    if builder_stage in allowed_builder_stages:
        sets.append("builder_stage=?")
        params.append(builder_stage)
    if builder_recommended_plan is not None:
        sets.append("builder_recommended_plan=?")
        params.append(str(builder_recommended_plan or '')[:80])
    if builder_payment_status in allowed_builder_payments:
        sets.append("builder_payment_status=?")
        params.append(builder_payment_status)
    if not sets:
        cur = get_support_ticket(int(ticket_id))
        if not cur:
            raise KeyError("ticket not found")
        return cur
    conn = connect()
    try:
        row = conn.execute("SELECT id FROM support_tickets WHERE id=?", (int(ticket_id),)).fetchone()
        if not row:
            raise KeyError("ticket not found")
        params.append(int(ticket_id))
        conn.execute("UPDATE support_tickets SET " + ", ".join(sets) + ", updated_at=datetime('now') WHERE id=?", params)
        conn.commit()
        return get_support_ticket(int(ticket_id)) or {"id": int(ticket_id)}
    finally:
        conn.close()

def log_supplier_click(
    listing_id: int,
    region: str,
    supplier_id: str,
    supplier_name: str,
    url: str,
    ip: str = "",
    user_agent: str = "",
    referer: str = "",
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO supplier_clicks
              (listing_id, region, supplier_id, supplier_name, url, ip, user_agent, referer, meta_json)
            VALUES
              (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(listing_id),
                (region or "").upper(),
                supplier_id or "",
                supplier_name or "",
                url or "",
                ip or "",
                user_agent or "",
                referer or "",
                json.dumps(meta or {}),
            ),
        )
        conn.commit()
    finally:
        conn.close()

def connect(timeout_seconds: float = 30.0):
    """Open SQLite locally or PostgreSQL when DATABASE_URL points to PostgreSQL."""
    global _SQLITE_PRAGMAS_READY
    if DB_ENGINE == "postgresql":
        if psycopg is None:
            raise RuntimeError("PostgreSQL runtime requires psycopg[binary]. Check api/requirements.txt and redeploy.")
        kwargs = {"connect_timeout": int(float(timeout_seconds or 30.0)), "row_factory": dict_row}
        conn = psycopg.connect(DB_URL, **kwargs)
        return PgConnection(conn)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=float(timeout_seconds or 30.0))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(f"PRAGMA busy_timeout={int(float(timeout_seconds or 30.0) * 1000)}")
        if not _SQLITE_PRAGMAS_READY:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            _SQLITE_PRAGMAS_READY = True
    except sqlite3.OperationalError:
        # If another process is already touching the DB while the dev server
        # starts, keep the connection usable and let the timeout handle it.
        pass
    return conn


def listing_customer_no(listing_id: int) -> str:
    """Stable internal RiceMap24 customer/actor number."""
    try:
        n = max(0, int(listing_id))
    except Exception:
        n = 0
    return f"RM24-{n:06d}"


def _migrate(conn: sqlite3.Connection) -> None:
    """Lightweight migrations for older DB files."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(listings)").fetchall()}

    def add(col_sql: str) -> None:
        conn.execute(f"ALTER TABLE listings ADD COLUMN {col_sql}")

    if "plan" not in cols:
        add("plan TEXT DEFAULT 'basic'")
    if "billing" not in cols:
        add("billing TEXT DEFAULT 'monthly'")
    if "plan_active" not in cols:
        add("plan_active INTEGER NOT NULL DEFAULT 1")
    if "account_status" not in cols:
        add("account_status TEXT NOT NULL DEFAULT 'active'")
    if "preview_token" not in cols:
        add("preview_token TEXT")
    if "pending_activation" not in cols:
        add("pending_activation INTEGER NOT NULL DEFAULT 0")
    if "requested_at" not in cols:
        add("requested_at TEXT")
    if "activated_at" not in cols:
        add("activated_at TEXT")

    # Geo
    if "lat" not in cols:
        add("lat REAL")
    if "lng" not in cols:
        add("lng REAL")

    # Admin CRM / manual billing
    if "admin_note" not in cols:
        add("admin_note TEXT DEFAULT ''")
    if "paid_status" not in cols:
        add("paid_status TEXT DEFAULT 'unpaid'")
    if "paid_until" not in cols:
        add("paid_until TEXT")
    if "last_payment_at" not in cols:
        add("last_payment_at TEXT")

    # Demo / marketplace visibility flags
    if "is_demo" not in cols:
        add("is_demo INTEGER NOT NULL DEFAULT 0")
    if "listing_type" not in cols:
        add("listing_type TEXT NOT NULL DEFAULT 'real'")
    if "accepts_orders" not in cols:
        add("accepts_orders INTEGER NOT NULL DEFAULT 1")
    if "show_in_actor_marketing" not in cols:
        add("show_in_actor_marketing INTEGER NOT NULL DEFAULT 1")
    if "show_in_customer_marketplace" not in cols:
        add("show_in_customer_marketplace INTEGER NOT NULL DEFAULT 1")

    # Auth foundation tables (step 9.16): no login flow yet, but schema is ready.
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS app_users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT UNIQUE NOT NULL,
          password_hash TEXT,
          display_name TEXT DEFAULT '',
          role TEXT NOT NULL DEFAULT 'owner',
          listing_id INTEGER,
          active INTEGER NOT NULL DEFAULT 1,
          email_verified INTEGER NOT NULL DEFAULT 0,
          last_login_at TEXT,
          created_at TEXT DEFAULT (datetime('now')),
          updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email);
        CREATE INDEX IF NOT EXISTS idx_app_users_listing ON app_users(listing_id);
        CREATE INDEX IF NOT EXISTS idx_app_users_role ON app_users(role);

        CREATE TABLE IF NOT EXISTS app_sessions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          session_token_hash TEXT UNIQUE NOT NULL,
          user_id INTEGER NOT NULL,
          role TEXT NOT NULL DEFAULT 'owner',
          ip TEXT DEFAULT '',
          user_agent TEXT DEFAULT '',
          expires_at TEXT NOT NULL,
          revoked_at TEXT,
          created_at TEXT DEFAULT (datetime('now')),
          updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_app_sessions_user ON app_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_app_sessions_expires ON app_sessions(expires_at);
        """
    )

    # Stripe subscription fields
    if "stripe_customer_id" not in cols:
        add("stripe_customer_id TEXT")
    if "stripe_subscription_id" not in cols:
        add("stripe_subscription_id TEXT")
    if "stripe_checkout_session_id" not in cols:
        add("stripe_checkout_session_id TEXT")
    if "stripe_status" not in cols:
        add("stripe_status TEXT")
    if "stripe_price_id" not in cols:
        add("stripe_price_id TEXT")
    if "stripe_current_period_end" not in cols:
        add("stripe_current_period_end TEXT")
    if "stripe_last_event_at" not in cols:
        add("stripe_last_event_at TEXT")

    # Stable internal actor/customer number
    if "customer_no" not in cols:
        add("customer_no TEXT")
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_listings_customer_no_unique ON listings(customer_no)")
        missing = conn.execute("SELECT id FROM listings WHERE customer_no IS NULL OR TRIM(customer_no)='' ORDER BY id ASC").fetchall()
        for r in missing:
            lid = int(r["id"] if isinstance(r, sqlite3.Row) else r[0])
            cno = listing_customer_no(lid)
            conn.execute("UPDATE listings SET customer_no=?, updated_at=datetime('now') WHERE id=?", (cno, lid))
            try:
                row_json = conn.execute("SELECT data_json FROM listings WHERE id=?", (lid,)).fetchone()
                data = json.loads(row_json["data_json"] or "{}") if row_json else {}
                data["customer_no"] = cno
                conn.execute("UPDATE listings SET data_json=? WHERE id=?", (json.dumps(data, ensure_ascii=False), lid))
            except Exception:
                pass
    except Exception:
        pass

    # Ensure older/demo listings also have a preview token for admin "View as kitchen".
    try:
        missing_tokens = conn.execute(
            "SELECT id FROM listings WHERE preview_token IS NULL OR TRIM(preview_token)='' ORDER BY id ASC"
        ).fetchall()
        for r in missing_tokens:
            lid = int(r["id"] if isinstance(r, sqlite3.Row) else r[0])
            token = _ensure_preview_token(conn)
            conn.execute("UPDATE listings SET preview_token=?, updated_at=datetime('now') WHERE id=?", (token, lid))
            try:
                row_json = conn.execute("SELECT data_json FROM listings WHERE id=?", (lid,)).fetchone()
                data = json.loads(row_json["data_json"] or "{}") if row_json else {}
                data["preview_token"] = token
                conn.execute("UPDATE listings SET data_json=? WHERE id=?", (json.dumps(data, ensure_ascii=False), lid))
            except Exception:
                pass
    except Exception:
        pass

    # Normalize legacy plan names
    try:
        conn.execute("UPDATE listings SET plan='business' WHERE plan IN ('premium','standard')")
    except Exception:
        pass
    # Preserve already-live local/demo listings when upgrading older dev databases.
    # New unpaid or cancelled accounts are still hidden by the billing visibility rules.
    try:
        conn.execute("""UPDATE listings
                       SET paid_status='paid', last_payment_at=COALESCE(last_payment_at, datetime('now'))
                       WHERE published=1 AND plan_active=1
                         AND COALESCE(paid_status, 'unpaid')='unpaid'
                         AND (stripe_subscription_id IS NULL OR TRIM(stripe_subscription_id)='')
                         AND (paid_until IS NULL OR TRIM(paid_until)='')
                         AND COALESCE(account_status, 'active') NOT IN ('past_due','cancelled','paused','archived','deleted_by_request')""")
    except Exception:
        pass

    # Geocache table (safe to run multiple times)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS geocache (
          query_key TEXT PRIMARY KEY,
          display_name TEXT,
          lat REAL,
          lng REAL,
          provider TEXT,
          created_at TEXT DEFAULT (datetime('now')),
          updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_geocache_updated ON geocache(updated_at);
        """
    )

    # --- Customers / CRM -------------------------------------------------
    try:
        ccols = {r["name"] for r in conn.execute("PRAGMA table_info(customers)").fetchall()}
        if "customer_no" not in ccols:
            conn.execute("ALTER TABLE customers ADD COLUMN customer_no TEXT")
        if "org_no" not in ccols:
            conn.execute("ALTER TABLE customers ADD COLUMN org_no TEXT")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_no_unique ON customers(listing_id, customer_no)")
    except Exception:
        # customers table might not exist in very old DBs; schema script will create it
        pass

    # Backfill customer_no for existing rows (per listing)
    try:
        rows = conn.execute("SELECT DISTINCT listing_id FROM customers").fetchall()
        for r in rows:
            lid = int(r["listing_id"]) if isinstance(r, sqlite3.Row) else int(r[0])
            custs = conn.execute(
                "SELECT id, customer_no FROM customers WHERE listing_id=? ORDER BY id ASC",
                (lid,),
            ).fetchall()
            # find max existing
            max_n = 0
            for c in custs:
                cn = (c["customer_no"] if isinstance(c, sqlite3.Row) else c[1]) or ""
                if isinstance(cn, str) and cn.startswith("C-"):
                    try:
                        max_n = max(max_n, int(cn.split("-", 1)[1]))
                    except Exception:
                        pass
            # assign missing
            n = max_n
            for c in custs:
                cid = int(c["id"] if isinstance(c, sqlite3.Row) else c[0])
                cn = (c["customer_no"] if isinstance(c, sqlite3.Row) else c[1]) or ""
                if not cn:
                    n += 1
                    new_no = f"C-{n:04d}"
                    conn.execute(
                        "UPDATE customers SET customer_no=?, updated_at=datetime('now') WHERE id=? AND listing_id=?",
                        (new_no, cid, lid),
                    )
    except Exception:
        pass

    # --- Accounting ------------------------------------------------------
    try:
        tcols = {r["name"] for r in conn.execute("PRAGMA table_info(accounting_transactions)").fetchall()}
        if "customer_id" not in tcols:
            conn.execute("ALTER TABLE accounting_transactions ADD COLUMN customer_id INTEGER")
        if "dish_name" not in tcols:
            conn.execute("ALTER TABLE accounting_transactions ADD COLUMN dish_name TEXT")
        if "qty" not in tcols:
            conn.execute("ALTER TABLE accounting_transactions ADD COLUMN qty INTEGER")
        if "items_json" not in tcols:
            conn.execute("ALTER TABLE accounting_transactions ADD COLUMN items_json TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_acc_customer ON accounting_transactions(customer_id)")
        # Backfill qty defaults
        try:
            conn.execute("UPDATE accounting_transactions SET qty=1 WHERE qty IS NULL")
        except Exception:
            pass
    except Exception:
        pass

    # --- Receipts (email tracking) --------------------------------------
    try:
        rcols = {r["name"] for r in conn.execute("PRAGMA table_info(receipts)").fetchall()}
        if "email_last_to" not in rcols:
            conn.execute("ALTER TABLE receipts ADD COLUMN email_last_to TEXT")
        if "email_sent_at" not in rcols:
            conn.execute("ALTER TABLE receipts ADD COLUMN email_sent_at TEXT")
        if "email_status" not in rcols:
            conn.execute("ALTER TABLE receipts ADD COLUMN email_status TEXT")
        if "email_error" not in rcols:
            conn.execute("ALTER TABLE receipts ADD COLUMN email_error TEXT")
        if "items_json" not in rcols:
            conn.execute("ALTER TABLE receipts ADD COLUMN items_json TEXT")
        # replacement / immutability helpers
        if "status" not in rcols:
            conn.execute("ALTER TABLE receipts ADD COLUMN status TEXT DEFAULT 'issued'")
        if "replaces_receipt_id" not in rcols:
            conn.execute("ALTER TABLE receipts ADD COLUMN replaces_receipt_id INTEGER")
    except Exception:
        pass




    # --- Stripe webhook event log (MVP / production readiness) ----------
    try:
        _ensure_stripe_webhook_events(conn)
    except Exception:
        pass

    # --- Support tickets (MVP) -----------------------------------------
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              listing_id INTEGER NOT NULL,
              subject TEXT NOT NULL,
              category TEXT DEFAULT 'general',
              status TEXT NOT NULL DEFAULT 'open',
              priority TEXT NOT NULL DEFAULT 'normal',
              created_by TEXT DEFAULT 'owner',
              internal_note TEXT DEFAULT '',
              builder_stage TEXT DEFAULT 'new_request',
              builder_recommended_plan TEXT DEFAULT '',
              builder_payment_status TEXT DEFAULT '',
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_support_tickets_listing ON support_tickets(listing_id);
            CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
            CREATE INDEX IF NOT EXISTS idx_support_tickets_updated ON support_tickets(updated_at);
            CREATE TABLE IF NOT EXISTS support_ticket_messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ticket_id INTEGER NOT NULL,
              sender TEXT NOT NULL DEFAULT 'owner',
              body TEXT NOT NULL,
              is_internal INTEGER NOT NULL DEFAULT 0,
              created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_support_ticket_messages_ticket ON support_ticket_messages(ticket_id);
            """
        )
        tcols = {r["name"] for r in conn.execute("PRAGMA table_info(support_tickets)").fetchall()}
        if "internal_note" not in tcols:
            conn.execute("ALTER TABLE support_tickets ADD COLUMN internal_note TEXT DEFAULT ''")
        if "builder_stage" not in tcols:
            conn.execute("ALTER TABLE support_tickets ADD COLUMN builder_stage TEXT DEFAULT 'new_request'")
        if "builder_recommended_plan" not in tcols:
            conn.execute("ALTER TABLE support_tickets ADD COLUMN builder_recommended_plan TEXT DEFAULT ''")
        if "builder_payment_status" not in tcols:
            conn.execute("ALTER TABLE support_tickets ADD COLUMN builder_payment_status TEXT DEFAULT ''")
    except Exception:
        pass



    # --- Discount codes (admin MVP) --------------------------------------
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS discount_codes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              code TEXT UNIQUE NOT NULL,
              description TEXT DEFAULT '',
              discount_type TEXT NOT NULL DEFAULT 'percent',
              percent_off REAL,
              amount_off REAL,
              currency TEXT,
              applies_to_plan TEXT DEFAULT 'all',
              billing TEXT DEFAULT 'all',
              max_redemptions INTEGER,
              redemption_count INTEGER NOT NULL DEFAULT 0,
              active INTEGER NOT NULL DEFAULT 1,
              starts_at TEXT,
              ends_at TEXT,
              internal_note TEXT DEFAULT '',
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_discount_codes_code ON discount_codes(code);
            CREATE INDEX IF NOT EXISTS idx_discount_codes_active ON discount_codes(active);
        """)
        dcols = {r["name"] for r in conn.execute("PRAGMA table_info(discount_codes)").fetchall()}
        for col, sql in {
            "description": "description TEXT DEFAULT ''",
            "discount_type": "discount_type TEXT DEFAULT 'percent'",
            "percent_off": "percent_off REAL",
            "amount_off": "amount_off REAL",
            "currency": "currency TEXT",
            "applies_to_plan": "applies_to_plan TEXT DEFAULT 'all'",
            "billing": "billing TEXT DEFAULT 'all'",
            "max_redemptions": "max_redemptions INTEGER",
            "redemption_count": "redemption_count INTEGER NOT NULL DEFAULT 0",
            "active": "active INTEGER NOT NULL DEFAULT 1",
            "starts_at": "starts_at TEXT",
            "ends_at": "ends_at TEXT",
            "internal_note": "internal_note TEXT DEFAULT ''",
        }.items():
            if col not in dcols:
                conn.execute(f"ALTER TABLE discount_codes ADD COLUMN {sql}")
    except Exception:
        pass



def _ensure_app_error_log(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS app_error_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          level TEXT NOT NULL DEFAULT 'error',
          source TEXT NOT NULL DEFAULT 'backend',
          path TEXT DEFAULT '',
          method TEXT DEFAULT '',
          status_code INTEGER,
          message TEXT DEFAULT '',
          traceback TEXT DEFAULT '',
          request_id TEXT DEFAULT '',
          ip TEXT DEFAULT '',
          user_agent TEXT DEFAULT '',
          details_json TEXT,
          created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_app_error_log_created ON app_error_log(created_at);
        CREATE INDEX IF NOT EXISTS idx_app_error_log_level ON app_error_log(level);
        CREATE INDEX IF NOT EXISTS idx_app_error_log_path ON app_error_log(path);
    """)


def record_app_error_log(
    *,
    level: str = "error",
    source: str = "backend",
    path: str = "",
    method: str = "",
    status_code: Optional[int] = None,
    message: str = "",
    traceback_text: str = "",
    request_id: str = "",
    ip: str = "",
    user_agent: str = "",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    conn = connect()
    try:
        _ensure_app_error_log(conn)
        conn.execute(
            """
            INSERT INTO app_error_log
              (level, source, path, method, status_code, message, traceback, request_id, ip, user_agent, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(level or "error")[:20],
                str(source or "backend")[:40],
                str(path or "")[:240],
                str(method or "")[:20],
                int(status_code) if status_code is not None else None,
                str(message or "")[:500],
                str(traceback_text or "")[:5000],
                str(request_id or "")[:80],
                str(ip or "")[:80],
                str(user_agent or "")[:400],
                json.dumps(details or {}, ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_app_error_logs(limit: int = 100, level: str = "all", q: str = "") -> List[Dict[str, Any]]:
    conn = connect()
    try:
        _ensure_app_error_log(conn)
        where: List[str] = []
        params: List[Any] = []
        if level and level != "all":
            where.append("level=?")
            params.append(str(level)[:20])
        qq = (q or "").strip().lower()
        if qq:
            where.append("LOWER(COALESCE(path,'') || ' ' || COALESCE(message,'') || ' ' || COALESCE(details_json,'')) LIKE ?")
            params.append(f"%{qq}%")
        lim = max(1, min(int(limit or 100), 500))
        sql = "SELECT * FROM app_error_log"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(lim)
        rows = conn.execute(sql, params).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            try:
                details = json.loads(r["details_json"] or "{}")
            except Exception:
                details = {}
            out.append({
                "id": int(r["id"]),
                "level": r["level"] or "error",
                "source": r["source"] or "backend",
                "path": r["path"] or "",
                "method": r["method"] or "",
                "status_code": r["status_code"],
                "message": r["message"] or "",
                "traceback": r["traceback"] or "",
                "request_id": r["request_id"] or "",
                "ip": r["ip"] or "",
                "user_agent": r["user_agent"] or "",
                "details": details,
                "created_at": r["created_at"],
            })
        return out
    finally:
        conn.close()


def cleanup_app_error_logs(retention_days: int = 30) -> int:
    conn = connect()
    try:
        _ensure_app_error_log(conn)
        days = max(1, min(int(retention_days or 30), 365))
        cur = conn.execute("DELETE FROM app_error_log WHERE created_at < datetime('now', ?)", (f"-{days} days",))
        conn.commit()
        return int(cur.rowcount or 0)
    finally:
        conn.close()


def _ensure_admin_activity_log(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS admin_activity_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          actor TEXT DEFAULT 'admin',
          action TEXT NOT NULL,
          entity_type TEXT,
          entity_id INTEGER,
          listing_id INTEGER,
          customer_no TEXT,
          title TEXT,
          details_json TEXT,
          created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_admin_activity_created ON admin_activity_log(created_at);
        CREATE INDEX IF NOT EXISTS idx_admin_activity_listing ON admin_activity_log(listing_id);
        CREATE INDEX IF NOT EXISTS idx_admin_activity_action ON admin_activity_log(action);


CREATE TABLE IF NOT EXISTS stripe_webhook_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT,
  event_type TEXT NOT NULL,
  listing_id INTEGER,
  subscription_id TEXT,
  customer_id TEXT,
  status TEXT NOT NULL DEFAULT 'processed', -- received | processed | ignored | error | simulated
  source TEXT DEFAULT 'webhook', -- webhook | admin_simulation
  message TEXT DEFAULT '',
  details_json TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_stripe_events_created ON stripe_webhook_events(created_at);
CREATE INDEX IF NOT EXISTS idx_stripe_events_type ON stripe_webhook_events(event_type);
CREATE INDEX IF NOT EXISTS idx_stripe_events_listing ON stripe_webhook_events(listing_id);
    """)


def log_admin_activity(
    action: str,
    *,
    actor: str = "admin",
    entity_type: str = "",
    entity_id: Optional[int] = None,
    listing_id: Optional[int] = None,
    customer_no: str = "",
    title: str = "",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Append-only MVP admin activity log.

    This is intentionally lightweight: it records admin actions in SQLite so the
    admin page can audit support, access and billing decisions during dev/MVP.
    """
    if not action:
        return
    conn = connect()
    try:
        _ensure_admin_activity_log(conn)
        if listing_id and not customer_no:
            try:
                row = conn.execute("SELECT customer_no FROM listings WHERE id=?", (int(listing_id),)).fetchone()
                if row:
                    customer_no = row["customer_no"] or listing_customer_no(int(listing_id))
            except Exception:
                pass
        conn.execute(
            """
            INSERT INTO admin_activity_log
              (actor, action, entity_type, entity_id, listing_id, customer_no, title, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (actor or "admin")[:80],
                str(action)[:100],
                str(entity_type or "")[:60],
                int(entity_id) if entity_id is not None else None,
                int(listing_id) if listing_id is not None else None,
                str(customer_no or "")[:80],
                str(title or "")[:240],
                json.dumps(details or {}, ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_admin_activity_log(limit: int = 100, action: str = "all", listing_id: Optional[int] = None, q: str = "") -> List[Dict[str, Any]]:
    conn = connect()
    try:
        _ensure_admin_activity_log(conn)
        where: List[str] = []
        params: List[Any] = []
        if action and action != "all":
            where.append("action=?")
            params.append(action)
        if listing_id is not None:
            where.append("listing_id=?")
            params.append(int(listing_id))
        qq = (q or "").strip().lower()
        if qq:
            where.append("LOWER(COALESCE(customer_no,'') || ' ' || COALESCE(title,'') || ' ' || COALESCE(action,'') || ' ' || COALESCE(details_json,'')) LIKE ?")
            params.append(f"%{qq}%")
        lim = max(1, min(int(limit or 100), 500))
        sql = """
            SELECT a.*, l.name AS listing_name, l.slug AS listing_slug
            FROM admin_activity_log a
            LEFT JOIN listings l ON l.id=a.listing_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY a.id DESC LIMIT ?"
        params.append(lim)
        rows = conn.execute(sql, params).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            try:
                details = json.loads(r["details_json"] or "{}")
            except Exception:
                details = {}
            out.append({
                "id": int(r["id"]),
                "actor": r["actor"] or "admin",
                "action": r["action"],
                "entity_type": r["entity_type"] or "",
                "entity_id": r["entity_id"],
                "listing_id": r["listing_id"],
                "customer_no": r["customer_no"] or (listing_customer_no(int(r["listing_id"])) if r["listing_id"] else ""),
                "listing_name": r["listing_name"] or "",
                "listing_slug": r["listing_slug"] or "",
                "title": r["title"] or "",
                "details": details,
                "created_at": r["created_at"],
            })
        return out
    finally:
        conn.close()



def _ensure_stripe_webhook_events(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS stripe_webhook_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_id TEXT,
          event_type TEXT NOT NULL,
          listing_id INTEGER,
          subscription_id TEXT,
          customer_id TEXT,
          status TEXT NOT NULL DEFAULT 'processed',
          source TEXT DEFAULT 'webhook',
          message TEXT DEFAULT '',
          details_json TEXT,
          created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_stripe_events_created ON stripe_webhook_events(created_at);
        CREATE INDEX IF NOT EXISTS idx_stripe_events_type ON stripe_webhook_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_stripe_events_listing ON stripe_webhook_events(listing_id);
    """)


def record_stripe_webhook_event(event_type: str, *, event_id: str = "", listing_id: Optional[int] = None, subscription_id: str = "", customer_id: str = "", status: str = "processed", source: str = "webhook", message: str = "", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    conn = connect()
    try:
        _ensure_stripe_webhook_events(conn)
        conn.execute(
            """
            INSERT INTO stripe_webhook_events
              (event_id, event_type, listing_id, subscription_id, customer_id, status, source, message, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(event_id or "")[:160],
                str(event_type or "unknown")[:120],
                int(listing_id) if listing_id is not None else None,
                str(subscription_id or "")[:160],
                str(customer_id or "")[:160],
                str(status or "processed")[:40],
                str(source or "webhook")[:40],
                str(message or "")[:500],
                json.dumps(details or {}, ensure_ascii=False),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT last_insert_rowid() AS id").fetchone()
        return {"id": int(row["id"] if row else 0)}
    finally:
        conn.close()


def list_stripe_webhook_events(limit: int = 80, status: str = "all", event_type: str = "all", q: str = "") -> List[Dict[str, Any]]:
    conn = connect()
    try:
        _ensure_stripe_webhook_events(conn)
        where: List[str] = []
        params: List[Any] = []
        if status and status != "all":
            where.append("e.status=?")
            params.append(status)
        if event_type and event_type != "all":
            where.append("e.event_type=?")
            params.append(event_type)
        qq = (q or "").strip().lower()
        if qq:
            where.append("LOWER(COALESCE(e.event_id,'') || ' ' || COALESCE(e.event_type,'') || ' ' || COALESCE(e.subscription_id,'') || ' ' || COALESCE(e.customer_id,'') || ' ' || COALESCE(e.message,'') || ' ' || COALESCE(l.name,'') || ' ' || COALESCE(l.customer_no,'')) LIKE ?")
            params.append(f"%{qq}%")
        sql = """
            SELECT e.*, l.name AS listing_name, l.slug AS listing_slug, l.customer_no AS listing_customer_no
            FROM stripe_webhook_events e
            LEFT JOIN listings l ON l.id=e.listing_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY e.id DESC LIMIT ?"
        params.append(max(1, min(int(limit or 80), 300)))
        out=[]
        for r in conn.execute(sql, params).fetchall():
            try:
                details=json.loads(r["details_json"] or "{}")
            except Exception:
                details={}
            out.append({
                "id": int(r["id"]), "event_id": r["event_id"] or "", "event_type": r["event_type"] or "",
                "listing_id": r["listing_id"], "listing_name": r["listing_name"] or "", "listing_slug": r["listing_slug"] or "",
                "listing_customer_no": r["listing_customer_no"] or "", "subscription_id": r["subscription_id"] or "",
                "customer_id": r["customer_id"] or "", "status": r["status"] or "", "source": r["source"] or "",
                "message": r["message"] or "", "details": details, "created_at": r["created_at"],
            })
        return out
    finally:
        conn.close()


def _ensure_admin_notifications(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS admin_notifications (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          notification_type TEXT NOT NULL,
          recipient_type TEXT DEFAULT 'admin',
          recipient_email TEXT DEFAULT '',
          subject TEXT NOT NULL,
          body TEXT DEFAULT '',
          status TEXT NOT NULL DEFAULT 'queued', -- queued | sent | skipped | error
          listing_id INTEGER,
          ticket_id INTEGER,
          details_json TEXT,
          created_at TEXT DEFAULT (datetime('now')),
          sent_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_admin_notifications_created ON admin_notifications(created_at);
        CREATE INDEX IF NOT EXISTS idx_admin_notifications_status ON admin_notifications(status);
        CREATE INDEX IF NOT EXISTS idx_admin_notifications_type ON admin_notifications(notification_type);
    """)


def queue_admin_notification(
    notification_type: str,
    *,
    recipient_type: str = "admin",
    recipient_email: str = "",
    subject: str = "",
    body: str = "",
    listing_id: Optional[int] = None,
    ticket_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    status: str = "queued",
) -> Dict[str, Any]:
    conn = connect()
    try:
        _ensure_admin_notifications(conn)
        conn.execute(
            """INSERT INTO admin_notifications
                 (notification_type, recipient_type, recipient_email, subject, body, status, listing_id, ticket_id, details_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(notification_type or "general")[:80],
                str(recipient_type or "admin")[:40],
                str(recipient_email or "")[:240],
                str(subject or "")[:240],
                str(body or ""),
                str(status or "queued")[:40],
                int(listing_id) if listing_id is not None else None,
                int(ticket_id) if ticket_id is not None else None,
                json.dumps(details or {}, ensure_ascii=False),
            ),
        )
        nid = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.commit()
        return get_admin_notification(nid) or {"id": nid}
    finally:
        conn.close()


def get_admin_notification(notification_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        _ensure_admin_notifications(conn)
        r = conn.execute(
            """SELECT n.*, l.name AS listing_name, l.customer_no AS listing_customer_no
               FROM admin_notifications n
               LEFT JOIN listings l ON l.id=n.listing_id
               WHERE n.id=?""",
            (int(notification_id),),
        ).fetchone()
        if not r:
            return None
        try:
            details = json.loads(r["details_json"] or "{}")
        except Exception:
            details = {}
        return {
            "id": int(r["id"]),
            "notification_type": r["notification_type"],
            "recipient_type": r["recipient_type"] or "admin",
            "recipient_email": r["recipient_email"] or "",
            "subject": r["subject"] or "",
            "body": r["body"] or "",
            "status": r["status"] or "queued",
            "listing_id": r["listing_id"],
            "listing_name": r["listing_name"] or "",
            "listing_customer_no": r["listing_customer_no"] or "",
            "ticket_id": r["ticket_id"],
            "details": details,
            "created_at": r["created_at"],
            "sent_at": r["sent_at"],
        }
    finally:
        conn.close()


def list_admin_notifications(limit: int = 100, status: str = "all", notification_type: str = "all", q: str = "") -> List[Dict[str, Any]]:
    conn = connect()
    try:
        _ensure_admin_notifications(conn)
        where: List[str] = []
        params: List[Any] = []
        if status and status != "all":
            where.append("n.status=?")
            params.append(status)
        if notification_type and notification_type != "all":
            where.append("n.notification_type=?")
            params.append(notification_type)
        qq = (q or "").strip().lower()
        if qq:
            where.append("LOWER(COALESCE(n.subject,'') || ' ' || COALESCE(n.body,'') || ' ' || COALESCE(n.recipient_email,'') || ' ' || COALESCE(l.name,'') || ' ' || COALESCE(l.customer_no,'')) LIKE ?")
            params.append(f"%{qq}%")
        lim = max(1, min(int(limit or 100), 500))
        sql = """SELECT n.*, l.name AS listing_name, l.customer_no AS listing_customer_no
                 FROM admin_notifications n
                 LEFT JOIN listings l ON l.id=n.listing_id"""
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY n.id DESC LIMIT ?"
        params.append(lim)
        rows = conn.execute(sql, params).fetchall()
        out=[]
        for r in rows:
            try:
                details = json.loads(r["details_json"] or "{}")
            except Exception:
                details = {}
            out.append({
                "id": int(r["id"]),
                "notification_type": r["notification_type"],
                "recipient_type": r["recipient_type"] or "admin",
                "recipient_email": r["recipient_email"] or "",
                "subject": r["subject"] or "",
                "body": r["body"] or "",
                "status": r["status"] or "queued",
                "listing_id": r["listing_id"],
                "listing_name": r["listing_name"] or "",
                "listing_customer_no": r["listing_customer_no"] or "",
                "ticket_id": r["ticket_id"],
                "details": details,
                "created_at": r["created_at"],
                "sent_at": r["sent_at"],
            })
        return out
    finally:
        conn.close()


def mark_admin_notification_status(notification_id: int, status: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    conn = connect()
    try:
        _ensure_admin_notifications(conn)
        row = conn.execute("SELECT details_json FROM admin_notifications WHERE id=?", (int(notification_id),)).fetchone()
        if not row:
            raise KeyError("Notification not found")
        try:
            old = json.loads(row["details_json"] or "{}")
        except Exception:
            old = {}
        old.update(details or {})
        conn.execute(
            """UPDATE admin_notifications
               SET status=?, details_json=?, sent_at=CASE WHEN ?='sent' THEN datetime('now') ELSE sent_at END
               WHERE id=?""",
            (str(status or "queued")[:40], json.dumps(old, ensure_ascii=False), str(status or ""), int(notification_id)),
        )
        conn.commit()
        return get_admin_notification(int(notification_id)) or {"id": int(notification_id)}
    finally:
        conn.close()


def queue_due_access_notifications(days_ahead: int = 7) -> int:
    settings = get_admin_settings()
    if not settings.get("email_notifications_enabled", True) or not settings.get("notify_trial_expiry", True):
        return 0
    conn = connect()
    try:
        _ensure_admin_notifications(conn)
        today = date.today()
        end = today + timedelta(days=max(0, min(int(days_ahead or 7), 60)))
        rows = conn.execute(
            """SELECT id, name, customer_no, access_type, access_expires_at
               FROM listings
               WHERE COALESCE(access_expires_at,'') >= ?
                 AND COALESCE(access_expires_at,'') <= ?
                 AND COALESCE(account_status,'active') NOT IN ('cancelled','archived','deleted_by_request')""",
            (today.isoformat(), end.isoformat()),
        ).fetchall()
        created = 0
        for r in rows:
            exists = conn.execute(
                """SELECT id FROM admin_notifications
                   WHERE notification_type='trial_expiry' AND listing_id=? AND status!='skipped'
                     AND details_json LIKE ?
                   LIMIT 1""",
                (int(r["id"]), f'%{r["access_expires_at"]}%'),
            ).fetchone()
            if exists:
                continue
            conn.execute(
                """INSERT INTO admin_notifications
                   (notification_type, recipient_type, recipient_email, subject, body, status, listing_id, details_json)
                   VALUES ('trial_expiry','admin',?,?,?,?,?,?)""",
                (
                    str(settings.get("admin_notification_email") or ""),
                    f"Access expires soon: {r['name']}",
                    f"{r['name']} ({r['customer_no'] or listing_customer_no(int(r['id']))}) has {r['access_type'] or 'manual'} access expiring on {r['access_expires_at']}.",
                    "queued",
                    int(r["id"]),
                    json.dumps({"access_expires_at": r["access_expires_at"], "access_type": r["access_type"]}, ensure_ascii=False),
                ),
            )
            created += 1
        conn.commit()
        return created
    finally:
        conn.close()


def _ensure_admin_users(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS admin_users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          email TEXT DEFAULT '',
          role TEXT NOT NULL DEFAULT 'owner',
          active INTEGER NOT NULL DEFAULT 1,
          last_seen_at TEXT,
          internal_note TEXT DEFAULT '',
          created_at TEXT DEFAULT (datetime('now')),
          updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);
        CREATE INDEX IF NOT EXISTS idx_admin_users_active ON admin_users(active);
    """)
    row = conn.execute("SELECT COUNT(*) AS c FROM admin_users").fetchone()
    if not row or int(row["c"] or 0) == 0:
        conn.execute(
            "INSERT INTO admin_users (name, email, role, active, internal_note) VALUES (?, ?, ?, 1, ?)",
            ("Marius / Owner", "", "owner", "Default local admin user for MVP. Replace before production."),
        )


def list_admin_users() -> List[Dict[str, Any]]:
    conn = connect()
    try:
        _ensure_admin_users(conn)
        conn.commit()
        rows = conn.execute("SELECT * FROM admin_users ORDER BY active DESC, role ASC, name ASC, id ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def upsert_admin_user(payload: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
    p = payload or {}
    name = str(p.get("name") or "").strip()[:120]
    email = str(p.get("email") or "").strip()[:180]
    role = str(p.get("role") or "owner").strip().lower()
    if role not in {"owner", "admin", "support", "billing", "viewer"}:
        role = "viewer"
    active = 1 if p.get("active", True) else 0
    note = str(p.get("internal_note") or "").strip()[:500]
    if not name:
        raise ValueError("Admin user name is required")
    conn = connect()
    try:
        _ensure_admin_users(conn)
        if user_id:
            row = conn.execute("SELECT id FROM admin_users WHERE id=?", (int(user_id),)).fetchone()
            if not row:
                raise KeyError("Admin user not found")
            conn.execute(
                """UPDATE admin_users
                   SET name=?, email=?, role=?, active=?, internal_note=?, updated_at=datetime('now')
                   WHERE id=?""",
                (name, email, role, active, note, int(user_id)),
            )
            out_id = int(user_id)
        else:
            cur = conn.execute(
                """INSERT INTO admin_users (name, email, role, active, internal_note)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, email, role, active, note),
            )
            out_id = int(cur.lastrowid)
        conn.commit()
        row = conn.execute("SELECT * FROM admin_users WHERE id=?", (out_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def mark_admin_user_seen(user_id: int) -> None:
    conn = connect()
    try:
        _ensure_admin_users(conn)
        conn.execute("UPDATE admin_users SET last_seen_at=datetime('now'), updated_at=datetime('now') WHERE id=?", (int(user_id),))
        conn.commit()
    finally:
        conn.close()



def _ensure_admin_announcements(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_announcements (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          body TEXT NOT NULL,
          cta TEXT DEFAULT '',
          target_tab TEXT DEFAULT 'dashboard',
          target_plan TEXT DEFAULT 'all',
          target_listing_id INTEGER,
          priority TEXT DEFAULT 'normal',
          status TEXT DEFAULT 'active',
          active_from TEXT,
          active_until TEXT,
          max_views INTEGER DEFAULT 1,
          created_at TEXT DEFAULT (datetime('now')),
          updated_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_announcements_status ON admin_announcements(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_announcements_target_plan ON admin_announcements(target_plan)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_announcements_listing ON admin_announcements(target_listing_id)")


def _row_to_admin_announcement(r: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": r["id"],
        "title": r["title"],
        "body": r["body"],
        "cta": r["cta"] or "",
        "target_tab": r["target_tab"] or "dashboard",
        "target_plan": r["target_plan"] or "all",
        "target_listing_id": r["target_listing_id"],
        "priority": r["priority"] or "normal",
        "status": r["status"] or "active",
        "active_from": r["active_from"] or "",
        "active_until": r["active_until"] or "",
        "max_views": int(r["max_views"] or 1),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def create_admin_announcement(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = str((payload or {}).get("title") or "").strip()[:180]
    body = str((payload or {}).get("body") or "").strip()[:1200]
    if not title or not body:
        raise ValueError("title and body are required")
    cta = str((payload or {}).get("cta") or "").strip()[:80]
    target_tab = str((payload or {}).get("target_tab") or "dashboard").strip().lower()[:40]
    target_plan = str((payload or {}).get("target_plan") or "all").strip().lower()[:40]
    if target_plan not in {"all", "basic", "business", "growth", "pro"}:
        target_plan = "all"
    priority = str((payload or {}).get("priority") or "normal").strip().lower()[:40]
    if priority not in {"normal", "important"}:
        priority = "normal"
    status = str((payload or {}).get("status") or "active").strip().lower()[:40]
    if status not in {"draft", "active", "archived"}:
        status = "active"
    active_from = str((payload or {}).get("active_from") or "").strip()[:30]
    active_until = str((payload or {}).get("active_until") or "").strip()[:30]
    if len(active_from) == 10:
        active_from = active_from + "T00:00:00Z"
    if len(active_until) == 10:
        active_until = active_until + "T23:59:59Z"
    try:
        target_listing_id = int((payload or {}).get("target_listing_id") or 0) or None
    except Exception:
        target_listing_id = None
    try:
        max_views = max(1, min(10, int((payload or {}).get("max_views") or 1)))
    except Exception:
        max_views = 1
    with connect() as conn:
        _ensure_admin_announcements(conn)
        cur = conn.execute(
            """INSERT INTO admin_announcements
                 (title, body, cta, target_tab, target_plan, target_listing_id, priority, status, active_from, active_until, max_views)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, body, cta, target_tab, target_plan, target_listing_id, priority, status, active_from, active_until, max_views),
        )
        conn.commit()
        return get_admin_announcement(int(cur.lastrowid)) or {"id": int(cur.lastrowid)}


def get_admin_announcement(announcement_id: int) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        _ensure_admin_announcements(conn)
        r = conn.execute("SELECT * FROM admin_announcements WHERE id=?", (int(announcement_id),)).fetchone()
        return _row_to_admin_announcement(r) if r else None


def list_admin_announcements(limit: int = 100, status: str = "all", target_plan: str = "all") -> List[Dict[str, Any]]:
    with connect() as conn:
        _ensure_admin_announcements(conn)
        where = []
        params: List[Any] = []
        if status and status != "all":
            where.append("status=?")
            params.append(status)
        if target_plan and target_plan != "all":
            where.append("target_plan=?")
            params.append(target_plan)
        sql = "SELECT * FROM admin_announcements"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(int(limit or 100))
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [_row_to_admin_announcement(r) for r in rows]


def set_admin_announcement_status(announcement_id: int, status: str) -> Dict[str, Any]:
    status = str(status or "active").strip().lower()
    if status not in {"draft", "active", "archived"}:
        status = "active"
    with connect() as conn:
        _ensure_admin_announcements(conn)
        conn.execute("UPDATE admin_announcements SET status=?, updated_at=datetime('now') WHERE id=?", (status, int(announcement_id)))
        conn.commit()
        return get_admin_announcement(int(announcement_id)) or {"id": int(announcement_id), "status": status}


def list_active_owner_announcements(listing_id: int, plan: str) -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    plan = str(plan or "basic").lower()
    with connect() as conn:
        _ensure_admin_announcements(conn)
        rows = conn.execute(
            """SELECT * FROM admin_announcements
               WHERE status='active'
                 AND (target_plan='all' OR target_plan=? )
                 AND (target_listing_id IS NULL OR target_listing_id=? )
                 AND (active_from IS NULL OR active_from='' OR active_from<=?)
                 AND (active_until IS NULL OR active_until='' OR active_until>=?)
               ORDER BY CASE priority WHEN 'important' THEN 0 ELSE 1 END, created_at DESC, id DESC
               LIMIT 20""",
            (plan, int(listing_id), now, now),
        ).fetchall()
        return [_row_to_admin_announcement(r) for r in rows]

def _ensure_admin_settings(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_settings (
          key TEXT PRIMARY KEY,
          value TEXT,
          updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    for k, v in DEFAULT_ADMIN_SETTINGS.items():
        conn.execute("INSERT OR IGNORE INTO admin_settings (key, value) VALUES (?, ?)", (k, v))
    # Local placeholder addresses from earlier MVP builds should not become the
    # suggested production sender. Keep real delivery disabled by default, but
    # prepare the visible sender fields for the future domain setup.
    conn.execute("UPDATE admin_settings SET value=? WHERE key='email_from_email' AND value='no-reply@ricemap24.local'", (DEFAULT_ADMIN_SETTINGS['email_from_email'],))
    conn.execute("UPDATE admin_settings SET value=? WHERE key='email_reply_to' AND value='support@ricemap24.local'", (DEFAULT_ADMIN_SETTINGS['email_reply_to'],))


def _coerce_admin_setting(key: str, value: Any) -> str:
    if key in BOOL_ADMIN_SETTINGS:
        if isinstance(value, str):
            v = value.strip().lower() in {"1", "true", "yes", "on"}
        else:
            v = bool(value)
        return "true" if v else "false"
    if key in INT_ADMIN_SETTINGS:
        try:
            n = int(value)
        except Exception:
            n = int(DEFAULT_ADMIN_SETTINGS.get(key, "0"))
        if key == "default_trial_days":
            n = max(0, min(365, n))
        if key == "billing_grace_days":
            n = max(0, min(60, n))
        if key == "monthly_owner_update_day":
            n = max(1, min(28, n))
        return str(n)
    return str(value or "")


def _coerced_default_admin_settings() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in DEFAULT_ADMIN_SETTINGS.items():
        if k in BOOL_ADMIN_SETTINGS:
            out[k] = str(v).strip().lower() in {"1", "true", "yes", "on"}
        elif k in INT_ADMIN_SETTINGS:
            try:
                out[k] = int(v)
            except Exception:
                out[k] = 0
        else:
            out[k] = v
    return out


def get_admin_settings() -> Dict[str, Any]:
    conn = connect()
    try:
        try:
            _ensure_admin_settings(conn)
            conn.commit()
            rows = conn.execute("SELECT key, value FROM admin_settings").fetchall()
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            # Do not let a temporary SQLite write lock take down public pages.
            # The default settings are conservative: signups/support stay on,
            # real email sending stays off, and unpaid kitchens are hidden.
            return _coerced_default_admin_settings()
        raw = {r["key"]: r["value"] for r in rows}
        for k, v in DEFAULT_ADMIN_SETTINGS.items():
            raw.setdefault(k, v)
        out: Dict[str, Any] = {}
        for k, v in raw.items():
            if k in BOOL_ADMIN_SETTINGS:
                out[k] = str(v).strip().lower() in {"1", "true", "yes", "on"}
            elif k in INT_ADMIN_SETTINGS:
                try:
                    out[k] = int(v)
                except Exception:
                    out[k] = int(DEFAULT_ADMIN_SETTINGS.get(k, "0"))
            else:
                out[k] = v
        return out
    finally:
        conn.close()


def update_admin_settings(patch: Dict[str, Any]) -> Dict[str, Any]:
    allowed = set(DEFAULT_ADMIN_SETTINGS.keys())
    conn = connect()
    try:
        _ensure_admin_settings(conn)
        for k, v in (patch or {}).items():
            if k not in allowed:
                continue
            val = _coerce_admin_setting(k, v)
            conn.execute(
                """INSERT INTO admin_settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')""",
                (k, val),
            )
        conn.commit()
        return get_admin_settings()
    finally:
        conn.close()



# --- Auth/session helpers ---------------------------------------------------

def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """Return a PBKDF2 password hash in a self-contained format.

    Format: pbkdf2_sha256$iterations$salt_hex$digest_hex
    This avoids introducing a new dependency before the production auth stack is finalised.
    """
    password = password or ""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    salt = secrets.token_bytes(16)
    iterations = 260_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        algo, iter_s, salt_hex, digest_hex = password_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iter_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _user_row_to_dict(row: sqlite3.Row | None) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        "id": int(row["id"]),
        "email": row["email"],
        "display_name": row["display_name"] or "",
        "role": row["role"] or "owner",
        "listing_id": int(row["listing_id"]) if row["listing_id"] is not None else None,
        "active": bool(int(row["active"] or 0)),
        "email_verified": bool(int(row["email_verified"] or 0)),
        "last_login_at": row["last_login_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_app_user(email: str, password: str, *, display_name: str = "", role: str = "owner", listing_id: Optional[int] = None, active: bool = True, email_verified: bool = False) -> Dict[str, Any]:
    email_norm = (email or "").strip().lower()
    if not email_norm or "@" not in email_norm:
        raise ValueError("Valid email is required")
    if len(password or "") < 8:
        raise ValueError("Password must be at least 8 characters")
    role_norm = (role or "owner").strip().lower()
    if role_norm not in {"owner", "admin"}:
        raise ValueError("Role must be owner or admin")
    pw_hash = hash_password(password)
    conn = connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO app_users (email, password_hash, display_name, role, listing_id, active, email_verified, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (email_norm, pw_hash, (display_name or "")[:120], role_norm, listing_id, 1 if active else 0, 1 if email_verified else 0),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM app_users WHERE id=?", (cur.lastrowid,)).fetchone()
        return _user_row_to_dict(row) or {}
    finally:
        conn.close()


def get_app_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM app_users WHERE lower(email)=lower(?)", ((email or "").strip(),)).fetchone()
        return _user_row_to_dict(row)
    finally:
        conn.close()


def authenticate_app_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM app_users WHERE lower(email)=lower(?)", ((email or "").strip(),)).fetchone()
        if not row or not int(row["active"] or 0):
            return None
        if not verify_password(password or "", row["password_hash"]):
            return None
        conn.execute("UPDATE app_users SET last_login_at=datetime('now'), updated_at=datetime('now') WHERE id=?", (int(row["id"]),))
        conn.commit()
        row = conn.execute("SELECT * FROM app_users WHERE id=?", (int(row["id"]),)).fetchone()
        return _user_row_to_dict(row)
    finally:
        conn.close()


def create_app_session(user_id: int, *, role: str = "owner", ip: str = "", user_agent: str = "", days: int = 14) -> Tuple[str, Dict[str, Any]]:
    token = secrets.token_urlsafe(48)
    token_hash = _hash_token(token)
    expires = (datetime.utcnow() + timedelta(days=max(1, int(days or 14)))).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO app_sessions (session_token_hash, user_id, role, ip, user_agent, expires_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (token_hash, int(user_id), role or "owner", (ip or "")[:120], (user_agent or "")[:400], expires),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM app_sessions WHERE id=?", (cur.lastrowid,)).fetchone()
        return token, {k: row[k] for k in row.keys()} if row else {}
    finally:
        conn.close()


def get_user_by_session_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    token_hash = _hash_token(token)
    conn = connect()
    try:
        row = conn.execute(
            """
            SELECT u.*
            FROM app_sessions s
            JOIN app_users u ON u.id=s.user_id
            WHERE s.session_token_hash=?
              AND s.revoked_at IS NULL
              AND s.expires_at > ?
              AND u.active=1
            """,
            (token_hash, _now_iso()),
        ).fetchone()
        return _user_row_to_dict(row)
    finally:
        conn.close()


def revoke_app_session(token: str) -> bool:
    if not token:
        return False
    conn = connect()
    try:
        cur = conn.execute("UPDATE app_sessions SET revoked_at=datetime('now'), updated_at=datetime('now') WHERE session_token_hash=? AND revoked_at IS NULL", (_hash_token(token),))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def record_login_attempt(email: str, ip: str = "", *, success: bool = False, reason: str = "") -> None:
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO login_attempts (email, ip, success, reason) VALUES (?, ?, ?, ?)",
            ((email or "").strip().lower()[:180], (ip or "")[:120], 1 if success else 0, (reason or "")[:80]),
        )
        conn.commit()
    finally:
        conn.close()


def recent_failed_login_count(email: str, ip: str = "", *, minutes: int = 15) -> int:
    conn = connect()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM login_attempts
            WHERE success=0
              AND created_at >= datetime('now', ?)
              AND (lower(email)=lower(?) OR ip=?)
            """,
            (f"-{max(1, int(minutes or 15))} minutes", (email or "").strip().lower(), (ip or "")[:120]),
        ).fetchone()
        return int(row["c"] or 0) if row else 0
    finally:
        conn.close()


def cleanup_expired_app_sessions() -> int:
    conn = connect()
    try:
        cur = conn.execute("UPDATE app_sessions SET revoked_at=datetime('now'), updated_at=datetime('now') WHERE revoked_at IS NULL AND expires_at <= ?", (_now_iso(),))
        conn.commit()
        return int(cur.rowcount or 0)
    finally:
        conn.close()


def list_app_users() -> List[Dict[str, Any]]:
    conn = connect()
    try:
        rows = conn.execute("SELECT * FROM app_users ORDER BY role ASC, email ASC").fetchall()
        return [_user_row_to_dict(r) or {} for r in rows]
    finally:
        conn.close()

def init_db() -> None:
    conn = connect()
    try:
        # PostgreSQL treats many DDL statements and later migration statements as
        # one transaction unless we commit between phases. Some legacy SQLite
        # migrations intentionally catch/ignore errors; if one of those errors
        # happens before the base schema is committed, PostgreSQL can roll back
        # the newly created tables. Commit the base schema first, then run the
        # compatibility migrations.
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        _migrate(conn)
        conn.commit()
    finally:
        conn.close()

def row_to_listing(row: sqlite3.Row) -> Dict[str, Any]:
    item = json.loads(row["data_json"])
    # inject meta / db ids for frontend use
    item["id"] = int(row["id"])
    item["customer_no"] = row["customer_no"] if "customer_no" in set(row.keys()) and row["customer_no"] else listing_customer_no(int(row["id"]))
    item["published"] = int(row["published"])
    # sqlite Row supports .keys()
    keys = set(row.keys())
    item["plan"] = row["plan"] if "plan" in keys else item.get("plan", "basic")
    item["billing"] = row["billing"] if "billing" in keys else item.get("billing", "monthly")
    item["plan_active"] = int(row["plan_active"]) if "plan_active" in keys else int(item.get("plan_active", 1))
    item["account_status"] = row["account_status"] if "account_status" in keys else item.get("account_status", "active")
    item["preview_token"] = row["preview_token"] if "preview_token" in keys else item.get("preview_token")
    item["pending_activation"] = int(row["pending_activation"]) if "pending_activation" in keys else int(item.get("pending_activation", 0))
    item["requested_at"] = row["requested_at"] if "requested_at" in keys else item.get("requested_at")
    item["activated_at"] = row["activated_at"] if "activated_at" in keys else item.get("activated_at")
    item["admin_note"] = row["admin_note"] if "admin_note" in keys else item.get("admin_note", "")
    item["paid_status"] = row["paid_status"] if "paid_status" in keys else item.get("paid_status", "unpaid")
    item["paid_until"] = row["paid_until"] if "paid_until" in keys else item.get("paid_until")
    item["last_payment_at"] = row["last_payment_at"] if "last_payment_at" in keys else item.get("last_payment_at")
    item["is_demo"] = bool(int(row["is_demo"])) if "is_demo" in keys else bool(item.get("is_demo", False))
    item["listing_type"] = row["listing_type"] if "listing_type" in keys else item.get("listing_type", "demo" if item.get("is_demo") else "real")
    item["accepts_orders"] = bool(int(row["accepts_orders"])) if "accepts_orders" in keys else bool(item.get("accepts_orders", True))
    item["show_in_actor_marketing"] = bool(int(row["show_in_actor_marketing"])) if "show_in_actor_marketing" in keys else bool(item.get("show_in_actor_marketing", True))
    item["show_in_customer_marketplace"] = bool(int(row["show_in_customer_marketplace"])) if "show_in_customer_marketplace" in keys else bool(item.get("show_in_customer_marketplace", True))

    # Admin-managed access controls stored in data_json for MVP/dev.
    # Later these can be promoted to dedicated columns if needed.
    item["access_type"] = item.get("access_type") or "paid"   # paid | trial | free | partner | internal
    item["access_expires_at"] = item.get("access_expires_at") or ""
    item["access_reason"] = item.get("access_reason") or ""
    # Feature overrides support both the older list format
    # ["britesight"] and the newer timed format:
    # {"britesight": {"enabled": true, "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "reason": "..."}}
    raw_feature_overrides = item.get("feature_overrides") or {}
    if isinstance(raw_feature_overrides, list):
        item["feature_overrides"] = {str(k): {"enabled": True, "start": "", "end": "", "reason": ""} for k in raw_feature_overrides if k}
    elif isinstance(raw_feature_overrides, dict):
        item["feature_overrides"] = raw_feature_overrides
    else:
        item["feature_overrides"] = {}

    item["stripe_customer_id"] = row["stripe_customer_id"] if "stripe_customer_id" in keys else item.get("stripe_customer_id")
    item["stripe_subscription_id"] = row["stripe_subscription_id"] if "stripe_subscription_id" in keys else item.get("stripe_subscription_id")
    item["stripe_checkout_session_id"] = row["stripe_checkout_session_id"] if "stripe_checkout_session_id" in keys else item.get("stripe_checkout_session_id")
    item["stripe_status"] = row["stripe_status"] if "stripe_status" in keys else item.get("stripe_status")
    item["stripe_price_id"] = row["stripe_price_id"] if "stripe_price_id" in keys else item.get("stripe_price_id")
    item["stripe_current_period_end"] = row["stripe_current_period_end"] if "stripe_current_period_end" in keys else item.get("stripe_current_period_end")
    item["stripe_last_event_at"] = row["stripe_last_event_at"] if "stripe_last_event_at" in keys else item.get("stripe_last_event_at")
    item["lat"] = row["lat"] if "lat" in keys else item.get("lat")
    item["lng"] = row["lng"] if "lng" in keys else item.get("lng")

    # Public trust/history marker. Use the database creation date as the
    # neutral platform join date unless a future migration adds a dedicated
    # joined_at column.
    created_at = row["created_at"] if "created_at" in keys else item.get("created_at")
    item["created_at"] = created_at or item.get("created_at") or ""
    item["joined_at"] = item.get("joined_at") or created_at or ""
    return item


# --- Billing / visibility rules --------------------------------------------
# Public kitchen visibility must be driven by valid paid/manual access, not by
# deleting records. A listing can stay in admin forever while the public page is
# hidden when payment/access is no longer valid.
HIDDEN_ACCOUNT_STATUSES = {"past_due", "cancelled", "paused", "archived", "deleted_by_request"}
MANUAL_ACCESS_TYPES = {"trial", "free", "partner", "internal"}
ACTIVE_STRIPE_STATUSES = {"active", "trialing"}


def _date_part(value: Any) -> str:
    return str(value or "").strip()[:10]


def _is_date_on_or_after_today(value: Any) -> bool:
    raw = _date_part(value)
    if not raw:
        return False
    try:
        return date.fromisoformat(raw) >= date.today()
    except Exception:
        return False


def _is_date_on_or_after_today_with_grace(value: Any, grace_days: int = 0) -> bool:
    """Return true if date is today/future, or within the configured grace period.

    Used for payment period end dates so a failed/late renewal does not hide a
    kitchen immediately when admin has configured a grace window.
    """
    raw = _date_part(value)
    if not raw:
        return False
    try:
        grace = max(0, int(grace_days or 0))
        return date.fromisoformat(raw) >= (date.today() - timedelta(days=grace))
    except Exception:
        return False


def _future_date(days: int) -> str:
    try:
        n = max(0, int(days or 0))
    except Exception:
        n = 0
    if n <= 0:
        return ""
    return (date.today() + timedelta(days=n)).isoformat()


def _is_manual_access_valid(listing: Dict[str, Any]) -> bool:
    access_type = str(listing.get("access_type") or "paid").strip().lower()
    if access_type not in MANUAL_ACCESS_TYPES:
        return False
    expires = _date_part(listing.get("access_expires_at"))
    # Empty expiry = open-ended manual admin access.
    return (not expires) or _is_date_on_or_after_today(expires)


def _is_paid_subscription_valid(listing: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> bool:
    settings = settings or get_admin_settings()
    grace_days = int(settings.get("billing_grace_days", 0) or 0)
    if str(listing.get("paid_status") or "unpaid").lower() == "paid":
        paid_until = _date_part(listing.get("paid_until"))
        # In local/dev MVP, blank paid_until means manually marked paid until admin changes it.
        if not paid_until or _is_date_on_or_after_today_with_grace(paid_until, grace_days):
            return True
    stripe_status = str(listing.get("stripe_status") or "").lower()
    if stripe_status in ACTIVE_STRIPE_STATUSES:
        period_end = _date_part(listing.get("stripe_current_period_end"))
        # If Stripe says active but period end is not stored yet, trust Stripe status in MVP.
        if not period_end or _is_date_on_or_after_today_with_grace(period_end, grace_days):
            return True
    return False


def has_valid_access(listing: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> bool:
    status = str(listing.get("account_status") or "active").lower()
    if status in {"cancelled", "paused", "archived", "deleted_by_request"}:
        return False
    return _is_manual_access_valid(listing) or _is_paid_subscription_valid(listing, settings=settings)


def _apply_billing_visibility(listing: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    listing = dict(listing)
    settings = settings or get_admin_settings()
    manual_valid = _is_manual_access_valid(listing)
    paid_valid = _is_paid_subscription_valid(listing, settings=settings)
    valid = has_valid_access(listing, settings=settings)
    status = str(listing.get("account_status") or "active").lower()

    listing["billing_visibility"] = "public" if valid and int(listing.get("published", 0) or 0) == 1 else "hidden"
    listing["billing_access_valid"] = bool(valid)
    listing["billing_access_source"] = "manual" if manual_valid else ("paid" if paid_valid else "none")

    hide_unpaid = bool(settings.get("hide_unpaid_kitchens_automatically", True))
    if valid:
        listing["plan_active"] = 1
        if status == "past_due":
            listing["account_status"] = "trial" if manual_valid and str(listing.get("access_type") or "") == "trial" else "active"
    else:
        listing["plan_active"] = 0
        if hide_unpaid:
            listing["published"] = 0
        if status not in {"cancelled", "paused", "archived", "deleted_by_request"}:
            listing["account_status"] = "past_due"
    return listing


def _persist_billing_visibility(conn: sqlite3.Connection, row: sqlite3.Row, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    before = row_to_listing(row)
    after = _apply_billing_visibility(before, settings=settings)
    changed = (
        int(after.get("plan_active", 0) or 0) != int(before.get("plan_active", 0) or 0)
        or int(after.get("published", 0) or 0) != int(before.get("published", 0) or 0)
        or str(after.get("account_status") or "") != str(before.get("account_status") or "")
    )
    if changed:
        data_json = json.dumps(after, ensure_ascii=False)
        conn.execute(
            """UPDATE listings
               SET published=?, plan_active=?, account_status=?, data_json=?, updated_at=datetime('now')
               WHERE id=?""",
            (int(after.get("published", 0) or 0), int(after.get("plan_active", 0) or 0), after.get("account_status", "past_due"), data_json, int(before["id"])),
        )
    return after


def refresh_billing_visibility(listing_id: Optional[int] = None) -> int:
    """Persist automatic payment/access visibility changes.

    Returns number of records whose public state was changed. Safe to call often.
    A temporary SQLite lock should not prevent public pages from loading; it can
    be retried on the next request.
    """
    # Read settings before opening the write connection. Opening a second
    # settings connection while this connection is writing can self-lock SQLite.
    settings = get_admin_settings()
    conn = connect(timeout_seconds=1.5)
    changed = 0
    try:
        try:
            if listing_id is not None:
                rows = conn.execute("SELECT * FROM listings WHERE id=?", (int(listing_id),)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM listings").fetchall()
            for row in rows:
                before = row_to_listing(row)
                after = _persist_billing_visibility(conn, row, settings=settings)
                if int(after.get("plan_active", 0) or 0) != int(before.get("plan_active", 0) or 0) or int(after.get("published", 0) or 0) != int(before.get("published", 0) or 0) or str(after.get("account_status") or "") != str(before.get("account_status") or ""):
                    changed += 1
            conn.commit()
            return changed
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            try:
                conn.rollback()
            except Exception:
                pass
            return 0
    finally:
        conn.close()


# --- Plan rules (MVP) ---

PLAN_MAX_DISHES = {
    # current plans
    "basic": 5,
    "business": 12,
    "growth": 24,
    "pro": 48,
    # legacy aliases kept for older local/demo data
    "standard": 12,
    "plus": 24,
    "premium": 12,
}


def normalize_plan(plan: str) -> str:
    p = (plan or "basic").lower().strip()
    if p in ("premium", "standard"):
        return "business"
    if p == "plus":
        return "growth"
    if p not in ("basic", "business", "growth", "pro"):
        return "basic"
    return p

def max_dishes_for_plan(plan: str) -> int:
    p = normalize_plan(plan)
    return PLAN_MAX_DISHES.get(p, PLAN_MAX_DISHES["basic"])

def validate_plan_limits(listing: Dict[str, Any], plan: str) -> None:
    """Raise ValueError if listing exceeds limits for the selected plan."""
    p = normalize_plan(plan or listing.get("plan") or "basic")
    max_dishes = max_dishes_for_plan(p)
    menu = listing.get("menu") or []
    try:
        count = len(menu)
    except Exception:
        count = 0
    if count > max_dishes:
        raise ValueError(
            f"Plan limit: {p} allows max {max_dishes} dishes, but you have {count}. Remove {count-max_dishes} dish(es) or upgrade."
        )

def seed_if_empty(seed_listings: List[Dict[str, Any]]) -> None:
    conn = connect()
    try:
        # Staging/local demo seed must not be blocked by an unpublished draft.
        # With PostgreSQL, a failed/partial signup can leave one draft row in listings;
        # the old COUNT(*) guard then prevented the intended demo kitchens from being inserted.
        # Only skip demo seeding when demo/public rows already exist.
        cur = conn.execute("SELECT COUNT(*) as c FROM listings WHERE published=1 AND plan_active=1 AND (is_demo=1 OR listing_type='demo')")
        c = int(cur.fetchone()["c"])
        if c > 0:
            return
        for item in seed_listings:
            upsert_listing(conn, item, published=1, plan_active=1, pending_activation=0)
        conn.commit()
    finally:
        conn.close()

def _ensure_preview_token(conn: sqlite3.Connection) -> str:
    for _ in range(20):
        token = secrets.token_urlsafe(16)
        row = conn.execute("SELECT id FROM listings WHERE preview_token=?", (token,)).fetchone()
        if not row:
            return token
    raise RuntimeError("could not generate unique preview token")

def upsert_listing(
    conn: sqlite3.Connection,
    listing: Dict[str, Any],
    published: Optional[int] = None,
    plan: Optional[str] = None,
    billing: Optional[str] = None,
    plan_active: Optional[int] = None,
    account_status: Optional[str] = None,
    preview_token: Optional[str] = None,
    pending_activation: Optional[int] = None,
    requested_at: Optional[str] = None,
    activated_at: Optional[str] = None,
    admin_note: Optional[str] = None,
    paid_status: Optional[str] = None,
    paid_until: Optional[str] = None,
    last_payment_at: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
    stripe_checkout_session_id: Optional[str] = None,
    stripe_status: Optional[str] = None,
    stripe_price_id: Optional[str] = None,
    stripe_current_period_end: Optional[str] = None,
    stripe_last_event_at: Optional[str] = None,
) -> Tuple[int, str]:
    slug = listing.get("slug")
    if not slug:
        raise ValueError("listing.slug is required")

    listing = dict(listing)

    # Normalize
    listing.setdefault("postcode", "")
    listing.setdefault("badges", [])
    listing.setdefault("cuisines", [])
    listing.setdefault("lat", None)
    listing.setdefault("lng", None)

    pub_val = int(published if published is not None else listing.get("published", 1))
    plan_val = (plan if plan is not None else listing.get("plan", "basic")) or "basic"
    billing_val = (billing if billing is not None else listing.get("billing", "monthly")) or "monthly"
    active_val = int(plan_active if plan_active is not None else listing.get("plan_active", 1))
    account_status_val = (account_status if account_status is not None else listing.get("account_status", "active")) or "active"
    allowed_account_statuses = {"active", "trial", "past_due", "cancelled", "paused", "archived", "deleted_by_request"}
    account_status_val = str(account_status_val).lower()
    if account_status_val not in allowed_account_statuses:
        account_status_val = "active"
    pending_val = int(pending_activation if pending_activation is not None else listing.get("pending_activation", 0))

    lat_val = listing.get("lat")
    lng_val = listing.get("lng")

    is_demo_val = 1 if bool(listing.get("is_demo", False)) else 0
    listing_type_val = str(listing.get("listing_type") or ("demo" if is_demo_val else "real")).lower()
    if listing_type_val not in {"real", "demo"}:
        listing_type_val = "demo" if is_demo_val else "real"
    accepts_orders_val = 1 if bool(listing.get("accepts_orders", True)) else 0
    show_actor_val = 1 if bool(listing.get("show_in_actor_marketing", True)) else 0
    show_market_val = 1 if bool(listing.get("show_in_customer_marketplace", True)) else 0

    note_val = admin_note if admin_note is not None else listing.get("admin_note", "")
    paid_status_val = (paid_status if paid_status is not None else listing.get("paid_status", "unpaid")) or "unpaid"
    paid_until_val = paid_until if paid_until is not None else listing.get("paid_until")
    last_payment_val = last_payment_at if last_payment_at is not None else listing.get("last_payment_at")


    stripe_customer_val = stripe_customer_id if stripe_customer_id is not None else listing.get("stripe_customer_id")
    stripe_sub_val = stripe_subscription_id if stripe_subscription_id is not None else listing.get("stripe_subscription_id")
    stripe_sess_val = stripe_checkout_session_id if stripe_checkout_session_id is not None else listing.get("stripe_checkout_session_id")
    stripe_status_val = stripe_status if stripe_status is not None else listing.get("stripe_status")
    stripe_price_val = stripe_price_id if stripe_price_id is not None else listing.get("stripe_price_id")
    stripe_cpe_val = stripe_current_period_end if stripe_current_period_end is not None else listing.get("stripe_current_period_end")
    stripe_evt_val = stripe_last_event_at if stripe_last_event_at is not None else listing.get("stripe_last_event_at")


    token_val = preview_token if preview_token is not None else listing.get("preview_token")
    if not token_val and pub_val == 0:
        token_val = _ensure_preview_token(conn)

    # Mirror meta into JSON for frontend convenience
    listing["published"] = pub_val
    listing["plan"] = plan_val
    listing["billing"] = billing_val
    listing["plan_active"] = active_val
    listing["account_status"] = account_status_val
    listing["preview_token"] = token_val
    listing["pending_activation"] = pending_val
    listing["admin_note"] = note_val
    listing["paid_status"] = paid_status_val
    listing["paid_until"] = paid_until_val
    listing["last_payment_at"] = last_payment_val
    listing["is_demo"] = bool(is_demo_val)
    listing["listing_type"] = listing_type_val
    listing["accepts_orders"] = bool(accepts_orders_val)
    listing["show_in_actor_marketing"] = bool(show_actor_val)
    listing["show_in_customer_marketplace"] = bool(show_market_val)

    listing["stripe_customer_id"] = stripe_customer_val
    listing["stripe_subscription_id"] = stripe_sub_val
    listing["stripe_checkout_session_id"] = stripe_sess_val
    listing["stripe_status"] = stripe_status_val
    listing["stripe_price_id"] = stripe_price_val
    listing["stripe_current_period_end"] = stripe_cpe_val
    listing["stripe_last_event_at"] = stripe_evt_val
    if requested_at is not None:
        listing["requested_at"] = requested_at
    if activated_at is not None:
        listing["activated_at"] = activated_at

    cuisines_json = json.dumps(listing.get("cuisines", []), ensure_ascii=False)
    badges_json = json.dumps(listing.get("badges", []), ensure_ascii=False)
    data_json = json.dumps(listing, ensure_ascii=False)

    row = conn.execute("SELECT id, customer_no FROM listings WHERE slug=?", (slug,)).fetchone()
    if row:
        _id = int(row["id"])
        customer_no_val = row["customer_no"] or listing_customer_no(_id)
        listing["customer_no"] = customer_no_val
        data_json = json.dumps(listing, ensure_ascii=False)
        conn.execute(
            """UPDATE listings SET
               customer_no=?, name=?, area=?, city=?, country=?, postcode=?,
               cuisines=?, badges=?, from_price=?, currency=?, hero_image=?,
               is_demo=?, listing_type=?, accepts_orders=?, show_in_actor_marketing=?, show_in_customer_marketplace=?,
               lat=?, lng=?,
               published=?, plan=?, billing=?, plan_active=?, account_status=?,
               preview_token=?, pending_activation=?, requested_at=?, activated_at=?,
               admin_note=?, paid_status=?, paid_until=?, last_payment_at=?,
               stripe_customer_id=?, stripe_subscription_id=?, stripe_checkout_session_id=?, stripe_status=?, stripe_price_id=?, stripe_current_period_end=?, stripe_last_event_at=?,
               data_json=?, updated_at=datetime('now')
               WHERE id=?""",
            (
                customer_no_val,
                listing.get("name", ""),
                listing.get("area", ""),
                listing.get("city", ""),
                listing.get("country", ""),
                listing.get("postcode", ""),
                cuisines_json,
                badges_json,
                listing.get("from_price"),
                listing.get("currency"),
                listing.get("hero_image"),
                is_demo_val,
                listing_type_val,
                accepts_orders_val,
                show_actor_val,
                show_market_val,
                lat_val,
                lng_val,
                pub_val,
                plan_val,
                billing_val,
                active_val,
                account_status_val,
                token_val,
                pending_val,
                requested_at if requested_at is not None else listing.get("requested_at"),
                activated_at if activated_at is not None else listing.get("activated_at"),
                note_val,
                paid_status_val,
                paid_until_val,
                last_payment_val,
                stripe_customer_val,
                stripe_sub_val,
                stripe_sess_val,
                stripe_status_val,
                stripe_price_val,
                stripe_cpe_val,
                stripe_evt_val,
                data_json,
                _id,
            ),
        )
        return _id, slug

    cur = conn.execute(
        """INSERT INTO listings
           (customer_no,slug,name,area,city,country,postcode,cuisines,badges,from_price,currency,hero_image,
            is_demo,listing_type,accepts_orders,show_in_actor_marketing,show_in_customer_marketplace,lat,lng,
            published,plan,billing,plan_active,account_status,preview_token,pending_activation,requested_at,activated_at,
            admin_note,paid_status,paid_until,last_payment_at,
            stripe_customer_id,stripe_subscription_id,stripe_checkout_session_id,stripe_status,stripe_price_id,stripe_current_period_end,stripe_last_event_at,
            data_json)
	           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            None,
            slug,
            listing.get("name", ""),
            listing.get("area", ""),
            listing.get("city", ""),
            listing.get("country", ""),
            listing.get("postcode", ""),
            cuisines_json,
            badges_json,
            listing.get("from_price"),
            listing.get("currency"),
            listing.get("hero_image"),
            is_demo_val,
            listing_type_val,
            accepts_orders_val,
            show_actor_val,
            show_market_val,
            lat_val,
            lng_val,
            pub_val,
            plan_val,
            billing_val,
            active_val,
            account_status_val,
            token_val,
            pending_val,
            requested_at,
            activated_at,
            note_val,
            paid_status_val,
            paid_until_val,
            last_payment_val,
            stripe_customer_val,
            stripe_sub_val,
            stripe_sess_val,
            stripe_status_val,
            stripe_price_val,
            stripe_cpe_val,
            stripe_evt_val,
            data_json,
        ),
    )
    new_id = int(cur.lastrowid)
    customer_no_val = listing_customer_no(new_id)
    listing["customer_no"] = customer_no_val
    data_json = json.dumps(listing, ensure_ascii=False)
    conn.execute("UPDATE listings SET customer_no=?, data_json=?, updated_at=datetime('now') WHERE id=?", (customer_no_val, data_json, new_id))
    return new_id, slug


def soft_delete_listing_by_owner(listing_id: int) -> Dict[str, Any]:
    """Schedule an owner-requested deletion with a 90-day restore window.

    The kitchen is hidden immediately from public pages and owner sessions are
    revoked, but the listing data is kept for admin review/restore. This is a
    reversible deactivation, not physical deletion/anonymization. Email reminder
    automation can be added later when real email delivery is configured.
    """
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (int(listing_id),)).fetchone()
        if not row:
            raise KeyError("not found")
        listing = row_to_listing(row)
        now = conn.execute("SELECT datetime('now') as t").fetchone()["t"]
        delete_at = conn.execute("SELECT datetime('now', '+90 days') as t").fetchone()["t"]

        # Store enough state inside data_json for a clean admin restore later.
        listing["deletion_requested_at"] = now
        listing["deletion_scheduled_for"] = delete_at
        listing["deletion_restore_window_days"] = 90
        listing["deletion_restore_published"] = int(listing.get("published", 0) or 0)
        listing["deletion_restore_plan_active"] = int(listing.get("plan_active", 0) or 0)
        listing["deletion_restore_account_status"] = str(listing.get("account_status") or "active")
        listing["deletion_restore_available"] = True

        note = str(listing.get("admin_note") or "").strip()
        extra = f"Owner requested deletion at {now}. Hidden immediately. Restore available until {delete_at}."
        listing["admin_note"] = (note + "\n" + extra).strip() if note else extra
        listing["published"] = 0
        listing["plan_active"] = 0
        listing["pending_activation"] = 0
        listing["account_status"] = "deleted_by_request"
        listing = _apply_billing_visibility(listing)

        # Direct UPDATE by id is safer than upsert here: deletion must always
        # affect the exact owner listing, even if slugs or cached JSON differ.
        data_json = json.dumps(listing, ensure_ascii=False)
        conn.execute(
            """UPDATE listings
               SET published=0,
                   plan_active=0,
                   pending_activation=0,
                   account_status='deleted_by_request',
                   admin_note=?,
                   data_json=?,
                   updated_at=datetime('now')
               WHERE id=?""",
            (listing.get("admin_note", ""), data_json, int(listing_id)),
        )

        users = conn.execute("SELECT id FROM app_users WHERE listing_id=?", (int(listing_id),)).fetchall()
        user_ids = [int(u["id"]) for u in users]
        conn.execute(
            "UPDATE app_users SET active=0, updated_at=datetime('now') WHERE listing_id=?",
            (int(listing_id),),
        )
        for uid in user_ids:
            conn.execute("UPDATE app_sessions SET revoked_at=datetime('now'), updated_at=datetime('now') WHERE user_id=? AND revoked_at IS NULL", (uid,))
        conn.commit()
        fresh = conn.execute("SELECT * FROM listings WHERE id=?", (int(listing_id),)).fetchone()
        return row_to_listing(fresh) if fresh else listing
    finally:
        conn.close()


def restore_deleted_listing_by_admin(listing_id: int) -> Dict[str, Any]:
    """Restore a listing that was scheduled for deletion by the owner."""
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (int(listing_id),)).fetchone()
        if not row:
            raise KeyError("not found")
        listing = row_to_listing(row)
        if str(listing.get("account_status") or "") != "deleted_by_request":
            return listing

        restore_status = str(listing.get("deletion_restore_account_status") or "active")
        if restore_status == "deleted_by_request":
            restore_status = "active"
        restore_plan_active = int(listing.get("deletion_restore_plan_active", 1) or 0)
        restore_published = int(listing.get("deletion_restore_published", 0) or 0)

        note = str(listing.get("admin_note") or "").strip()
        now = conn.execute("SELECT datetime('now') as t").fetchone()["t"]
        extra = f"Admin restored kitchen at {now}."
        listing["admin_note"] = (note + "\n" + extra).strip() if note else extra
        listing["account_status"] = restore_status
        listing["plan_active"] = restore_plan_active
        listing["published"] = restore_published
        listing["pending_activation"] = 0
        listing["deletion_restored_at"] = now
        listing["deletion_restore_available"] = False
        listing = _apply_billing_visibility(listing)

        upsert_listing(
            conn,
            listing,
            published=int(listing.get("published", 0) or 0),
            plan=listing.get("plan", "basic"),
            billing=listing.get("billing", "monthly"),
            plan_active=int(listing.get("plan_active", 0) or 0),
            account_status=listing.get("account_status", "active"),
            preview_token=listing.get("preview_token"),
            pending_activation=int(listing.get("pending_activation", 0) or 0),
            requested_at=listing.get("requested_at"),
            activated_at=listing.get("activated_at"),
            admin_note=listing.get("admin_note", ""),
            paid_status=listing.get("paid_status", "unpaid"),
            paid_until=listing.get("paid_until"),
            last_payment_at=listing.get("last_payment_at"),
            stripe_customer_id=listing.get("stripe_customer_id"),
            stripe_subscription_id=listing.get("stripe_subscription_id"),
            stripe_checkout_session_id=listing.get("stripe_checkout_session_id"),
            stripe_status=listing.get("stripe_status"),
            stripe_price_id=listing.get("stripe_price_id"),
            stripe_current_period_end=listing.get("stripe_current_period_end"),
            stripe_last_event_at=listing.get("stripe_last_event_at"),
        )
        conn.execute("UPDATE app_users SET active=1, updated_at=datetime('now') WHERE listing_id=?", (int(listing_id),))
        conn.commit()
        fresh = conn.execute("SELECT * FROM listings WHERE id=?", (int(listing_id),)).fetchone()
        return row_to_listing(fresh) if fresh else listing
    finally:
        conn.close()

def list_listings(
    q: Optional[str] = None,
    cuisine: Optional[str] = None,
    country: Optional[str] = None,
    note_weekend: Optional[bool] = None,
    has_group: Optional[bool] = None,
    has_family: Optional[bool] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = 40.0,
    include_drafts: bool = False,
) -> List[Dict[str, Any]]:
    if not include_drafts:
        try:
            refresh_billing_visibility()
        except Exception:
            # Public pages must not become blank or slow because a background
            # billing visibility refresh is temporarily blocked. Admin/payment
            # actions can retry the refresh later.
            pass
    conn = connect(timeout_seconds=5.0)
    try:
        where: List[str] = []
        params: List[Any] = []

        if not include_drafts:
            where.append("published=1 AND plan_active=1 AND COALESCE(account_status, 'active') NOT IN ('cancelled','paused','archived','deleted_by_request')")

        if country:
            where.append("UPPER(country)=UPPER(?)")
            params.append(country)

        # If a location is provided, we return nearest within radius_km.
        # In that case, we ignore text-search 'q' (it's treated as a location query).
        if not (lat is not None and lng is not None):
            # search: if numeric-ish -> postcode match
            if q:
                qs = q.strip()
                if re_is_postcode(qs):
                    where.append("(postcode LIKE ? OR REPLACE(postcode,' ','') LIKE ?)")
                    params.append(f"{qs}%")
                    params.append(f"{qs.replace(' ', '')}%")
                else:
                    where.append("(LOWER(name) LIKE ? OR LOWER(area) LIKE ? OR LOWER(city) LIKE ?)")
                    ql = f"%{qs.lower()}%"
                    params += [ql, ql, ql]

        sql = "SELECT * FROM listings"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC LIMIT 500"

        rows = conn.execute(sql, params).fetchall()
        items = [row_to_listing(r) for r in rows]

        def matches(item: Dict[str, Any]) -> bool:
            if cuisine and cuisine not in item.get("cuisines", []):
                return False
            if note_weekend and "this_weekend" not in item.get("badges", []):
                return False
            if has_group and not any(m.get("serves") == "group" for m in item.get("menu", [])):
                return False
            if has_family and not any(m.get("serves") == "family" for m in item.get("menu", [])):
                return False
            return True

        filtered = [i for i in items if matches(i)]

        if lat is not None and lng is not None:
            def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
                R = 6371.0
                p1 = math.radians(lat1)
                p2 = math.radians(lat2)
                dp = math.radians(lat2 - lat1)
                dl = math.radians(lon2 - lon1)
                a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c

            out2: List[Dict[str, Any]] = []
            for it in filtered:
                if it.get("lat") is None or it.get("lng") is None:
                    continue
                try:
                    dkm = haversine_km(float(lat), float(lng), float(it["lat"]), float(it["lng"]))
                except Exception:
                    continue
                if dkm <= float(radius_km or 40.0):
                    it = dict(it)
                    it["distance_km"] = round(dkm, 1)
                    out2.append(it)
            out2.sort(key=lambda x: x.get("distance_km", 999999))
            return out2

        return filtered
    finally:
        conn.close()

def get_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE slug=?", (slug,)).fetchone()
        if not row:
            return None
        item = _persist_billing_visibility(conn, row)
        conn.commit()
        return item
    finally:
        conn.close()

def get_by_id(_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (_id,)).fetchone()
        if not row:
            return None
        item = _persist_billing_visibility(conn, row)
        conn.commit()
        return item
    finally:
        conn.close()

def get_by_preview_token(token: str) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE preview_token=?", (token,)).fetchone()
        if not row:
            return None
        item = _persist_billing_visibility(conn, row)
        conn.commit()
        return item
    finally:
        conn.close()


def geocache_get(query_key: str) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT query_key, display_name, lat, lng, provider, updated_at FROM geocache WHERE query_key=?",
            (query_key,),
        ).fetchone()
        if not row:
            return None
        return {
            "query_key": row["query_key"],
            "display_name": row["display_name"],
            "lat": row["lat"],
            "lng": row["lng"],
            "provider": row["provider"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def geocache_set(query_key: str, display_name: str, lat: float, lng: float, provider: str = "nominatim") -> None:
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO geocache (query_key, display_name, lat, lng, provider)
            VALUES (?,?,?,?,?)
            ON CONFLICT(query_key) DO UPDATE SET
              display_name=excluded.display_name,
              lat=excluded.lat,
              lng=excluded.lng,
              provider=excluded.provider,
              updated_at=datetime('now')
            """,
            (query_key, display_name, float(lat), float(lng), provider),
        )
        conn.commit()
    finally:
        conn.close()


def ensure_plan(slug: str, plan: str) -> None:
    """Best-effort update used for demo defaults.

    If a listing already exists (e.g., older sqlite file), we can still
    enforce a demo plan without requiring the user to delete the DB.
    """
    conn = connect()
    try:
        row = conn.execute("SELECT id, plan FROM listings WHERE slug=?", (slug,)).fetchone()
        if not row:
            return
        current = (row["plan"] or "basic")
        if current != plan:
            conn.execute("UPDATE listings SET plan=?, updated_at=datetime('now') WHERE slug=?", (plan, slug))
            conn.commit()
    finally:
        conn.close()


def set_listing_currency(listing_id: int, currency: str) -> Dict[str, Any]:
    """Update listing currency (settings). Currency is stored both in the
    listings.currency column and inside data_json for the frontend."""
    cur = (currency or "").strip().upper()
    if not cur:
        raise ValueError("currency is required")
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (listing_id,)).fetchone()
        if not row:
            raise ValueError("Listing not found")
        item = row_to_listing(row)
        item["currency"] = cur
        data_json = json.dumps(item, ensure_ascii=False)
        conn.execute(
            "UPDATE listings SET currency=?, data_json=?, updated_at=datetime('now') WHERE id=?",
            (cur, data_json, listing_id),
        )
        conn.commit()
        row2 = conn.execute("SELECT * FROM listings WHERE id=?", (listing_id,)).fetchone()
        return row_to_listing(row2)
    finally:
        conn.close()

def admin_list(status: str = "pending") -> List[Dict[str, Any]]:
    """status: pending | live | draft | deleted | all"""
    refresh_billing_visibility()
    conn = connect()
    try:
        where: List[str] = []
        if status == "pending":
            where.append("pending_activation=1")
        elif status == "live":
            where.append("published=1 AND plan_active=1 AND COALESCE(account_status, 'active') NOT IN ('cancelled','paused','archived','deleted_by_request')")
        elif status == "draft":
            where.append("published=0 AND pending_activation=0 AND COALESCE(account_status, 'active')!='deleted_by_request'")
        elif status == "deleted":
            where.append("COALESCE(account_status, 'active')='deleted_by_request'")
        elif status == "all":
            pass
        else:
            where.append("pending_activation=1")

        sql = "SELECT * FROM listings"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY updated_at DESC LIMIT 300"

        rows = conn.execute(sql).fetchall()
        return [row_to_listing(r) for r in rows]
    finally:
        conn.close()


def admin_update(listing_id: int, fields: Dict[str, Any]) -> None:
    """Admin update for CRM/billing meta and plan controls."""
    allowed = {
        "plan",
        "billing",
        "plan_active",
        "account_status",
        "pending_activation",
        "published",
        "admin_note",
        "paid_status",
        "paid_until",
    }

    clean: Dict[str, Any] = {k: v for k, v in (fields or {}).items() if k in allowed}

    if not clean:
        return

    sets: List[str] = []
    params: List[Any] = []

    # Normalize
    if "plan" in clean:
        clean["plan"] = (clean["plan"] or "basic")
    if "billing" in clean:
        clean["billing"] = (clean["billing"] or "monthly")
    if "plan_active" in clean:
        clean["plan_active"] = 1 if int(clean["plan_active"] or 0) else 0
    if "account_status" in clean:
        allowed_statuses = {"active", "trial", "past_due", "cancelled", "paused", "archived", "deleted_by_request"}
        clean["account_status"] = str(clean["account_status"] or "active").lower()
        if clean["account_status"] not in allowed_statuses:
            clean["account_status"] = "active"
    if "pending_activation" in clean:
        clean["pending_activation"] = 1 if int(clean["pending_activation"] or 0) else 0
    if "published" in clean:
        clean["published"] = 1 if int(clean["published"] or 0) else 0
    if "paid_status" in clean:
        clean["paid_status"] = "paid" if str(clean["paid_status"]).lower() == "paid" else "unpaid"

    # If marking paid, set last_payment_at
    mark_paid = ("paid_status" in clean and clean["paid_status"] == "paid")

    for k, v in clean.items():
        sets.append(f"{k}=?")
        params.append(v)

    if mark_paid:
        sets.append("last_payment_at=datetime('now')")

    sets.append("updated_at=datetime('now')")
    sql = f"UPDATE listings SET {', '.join(sets)} WHERE id=?"
    params.append(int(listing_id))

    conn = connect()
    try:
        row = conn.execute("SELECT id FROM listings WHERE id=?", (int(listing_id),)).fetchone()
        if not row:
            raise KeyError("not found")
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()

def create_draft(listing: Dict[str, Any]) -> Tuple[int, str, str]:
    conn = connect()
    try:
        settings = get_admin_settings()
        trial_days = int(settings.get("default_trial_days", 0) or 0)
        listing = dict(listing)
        listing["published"] = 0
        listing.setdefault("plan", "basic")
        listing.setdefault("billing", "monthly")
        listing["pending_activation"] = 0

        # Default trial gives a newly registered kitchen real, time-limited access
        # without making the public page visible until the approval setting allows it.
        if trial_days > 0 and not listing.get("access_type"):
            listing["access_type"] = "trial"
            listing["access_expires_at"] = _future_date(trial_days)
            listing["access_reason"] = f"Default {trial_days}-day trial from admin settings"
            listing["account_status"] = "trial"
            listing["plan_active"] = 1
            listing["paid_status"] = "unpaid"
        else:
            listing["plan_active"] = 0
            listing.setdefault("account_status", "active")

        _id, slug = upsert_listing(
            conn,
            listing,
            published=0,
            plan=listing.get("plan"),
            billing=listing.get("billing"),
            plan_active=int(listing.get("plan_active", 0) or 0),
            account_status=listing.get("account_status", "active"),
            pending_activation=0,
            paid_status=listing.get("paid_status", "unpaid"),
        )
        row = conn.execute("SELECT preview_token FROM listings WHERE id=?", (_id,)).fetchone()
        token = row["preview_token"] if row else listing.get("preview_token") or ""
        conn.commit()
        return _id, slug, token
    finally:
        conn.close()

def update_draft(_id: int, listing: Dict[str, Any]) -> None:
    conn = connect()
    try:
        existing = conn.execute(
            "SELECT slug,published,plan,billing,plan_active,account_status,preview_token,pending_activation,requested_at,activated_at FROM listings WHERE id=?",
            (_id,),
        ).fetchone()
        if not existing:
            raise KeyError("not found")

        listing = dict(listing)
        listing.setdefault("slug", existing["slug"])

        # preserve state flags
        listing["published"] = int(existing["published"])
        listing["plan"] = listing.get("plan") or existing["plan"] or "basic"
        listing["billing"] = listing.get("billing") or existing["billing"] or "monthly"
        listing["plan_active"] = int(existing["plan_active"])
        listing["account_status"] = existing["account_status"] or "active"
        listing["preview_token"] = listing.get("preview_token") or existing["preview_token"]
        listing["pending_activation"] = int(existing["pending_activation"])
        listing["requested_at"] = listing.get("requested_at") or existing["requested_at"]
        listing["activated_at"] = listing.get("activated_at") or existing["activated_at"]

        # Enforce plan limits for the listing's current plan
        validate_plan_limits(listing, listing["plan"])

        upsert_listing(
            conn,
            listing,
            published=int(existing["published"]),
            plan=listing["plan"],
            billing=listing["billing"],
            plan_active=int(existing["plan_active"]),
            preview_token=listing["preview_token"],
            pending_activation=int(existing["pending_activation"]),
            requested_at=listing["requested_at"],
            activated_at=listing["activated_at"],
        )
        conn.commit()
    finally:
        conn.close()

def request_activation(_id: int, plan: str, billing: str) -> str:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (_id,)).fetchone()
        if not row:
            raise KeyError("not found")
        listing = row_to_listing(row)

        # Enforce plan limits before allowing activation / checkout
        plan_clean = (plan or listing.get("plan") or "basic").lower().strip()
        validate_plan_limits(listing, plan_clean)

        listing["plan"] = plan or listing.get("plan", "basic")
        listing["billing"] = billing or listing.get("billing", "monthly")

        settings = get_admin_settings()
        approval_required = bool(settings.get("new_kitchen_approval_required", True))
        access_valid = has_valid_access(listing)

        requested_at = conn.execute("SELECT datetime('now') as t").fetchone()["t"]
        activated_at = listing.get("activated_at")
        token = listing.get("preview_token") or row["preview_token"] or _ensure_preview_token(conn)

        if approval_required or not access_valid:
            # Standard controlled flow: admin must approve/activate.
            listing["published"] = 0
            listing["pending_activation"] = 1
            listing["plan_active"] = 1 if access_valid else 0
            if not access_valid and str(listing.get("account_status") or "active") not in {"cancelled", "paused", "archived", "deleted_by_request"}:
                listing["account_status"] = "past_due"
        else:
            # Optional low-friction flow: public signup can go live immediately
            # when the kitchen already has valid access, e.g. default trial.
            listing["published"] = 1
            listing["pending_activation"] = 0
            listing["plan_active"] = 1
            activated_at = conn.execute("SELECT datetime('now') as t").fetchone()["t"]
            if str(listing.get("account_status") or "active") == "past_due":
                listing["account_status"] = "trial" if str(listing.get("access_type") or "") == "trial" else "active"

        upsert_listing(
            conn,
            listing,
            published=int(listing.get("published", 0) or 0),
            plan=listing["plan"],
            billing=listing["billing"],
            plan_active=int(listing.get("plan_active", 0) or 0),
            account_status=listing.get("account_status", "active"),
            preview_token=token,
            pending_activation=int(listing.get("pending_activation", 0) or 0),
            requested_at=requested_at,
            activated_at=activated_at,
        )
        conn.commit()
        return token
    finally:
        conn.close()

def admin_activate(_id: int) -> str:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (_id,)).fetchone()
        if not row:
            raise KeyError("not found")
        listing = row_to_listing(row)

        listing["published"] = 1
        listing["plan_active"] = 1
        listing["account_status"] = "active"
        listing["pending_activation"] = 0

        activated_at = conn.execute("SELECT datetime('now') as t").fetchone()["t"]
        listing = _apply_billing_visibility(listing)
        if int(listing.get("plan_active", 0) or 0) != 1:
            raise ValueError("Cannot activate public page without valid paid or manual access")

        upsert_listing(
            conn,
            listing,
            published=1,
            plan=listing.get("plan", "basic"),
            billing=listing.get("billing", "monthly"),
            plan_active=1,
            preview_token=listing.get("preview_token"),
            pending_activation=0,
            requested_at=listing.get("requested_at"),
            activated_at=activated_at,
        )
        conn.commit()
        return listing["slug"]
    finally:
        conn.close()

def admin_deactivate(_id: int) -> None:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (_id,)).fetchone()
        if not row:
            raise KeyError("not found")
        listing = row_to_listing(row)

        listing["published"] = 0
        listing["plan_active"] = 0
        listing["account_status"] = "cancelled"
        listing["pending_activation"] = 0

        upsert_listing(
            conn,
            listing,
            published=0,
            plan=listing.get("plan", "basic"),
            billing=listing.get("billing", "monthly"),
            plan_active=0,
            preview_token=listing.get("preview_token"),
            pending_activation=0,
            requested_at=listing.get("requested_at"),
            activated_at=listing.get("activated_at"),
        )
        conn.commit()
    finally:
        conn.close()


def admin_update_meta(
    _id: int,
    *,
    plan: Optional[str] = None,
    billing: Optional[str] = None,
    plan_active: Optional[int] = None,
    admin_note: Optional[str] = None,
    paid_status: Optional[str] = None,
    paid_until: Optional[str] = None,
    account_status: Optional[str] = None,
    access_type: Optional[str] = None,
    access_expires_at: Optional[str] = None,
    access_reason: Optional[str] = None,
    feature_overrides: Optional[List[str]] = None,
) -> None:
    """Update admin-managed fields for a listing.

    This is used for manual payment notes and lightweight partner CRM.
    """
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (_id,)).fetchone()
        if not row:
            raise KeyError("not found")
        listing = row_to_listing(row)

        # Normalize / apply
        if plan is not None:
            listing["plan"] = normalize_plan(plan)
            listing["plan"] = plan
        if billing in ("monthly", "yearly"):
            listing["billing"] = billing
        if plan_active is not None:
            listing["plan_active"] = int(plan_active)
        if admin_note is not None:
            listing["admin_note"] = admin_note
        if paid_status in ("unpaid", "paid"):
            listing["paid_status"] = paid_status
            # if marked paid, set last_payment_at to now (unless already set)
            if paid_status == "paid":
                if not listing.get("last_payment_at"):
                    listing["last_payment_at"] = conn.execute("SELECT datetime('now') as t").fetchone()["t"]
                if listing.get("account_status") == "past_due":
                    listing["account_status"] = "active"
        if paid_until is not None:
            listing["paid_until"] = paid_until

        if account_status is not None:
            allowed_statuses = {"active", "trial", "past_due", "cancelled", "paused", "archived", "deleted_by_request"}
            st = str(account_status or "active").strip().lower()
            if st not in allowed_statuses:
                st = "active"
            listing["account_status"] = st
            if st in ("cancelled", "paused", "archived", "deleted_by_request"):
                listing["plan_active"] = 0
                listing["published"] = 0
                listing["pending_activation"] = 0
            elif st in ("active", "trial") and listing.get("access_type") in ("trial", "free", "partner", "internal"):
                listing["plan_active"] = 1

        if access_type is not None:
            at = str(access_type or "paid").strip().lower()
            if at not in ("paid", "trial", "free", "partner", "internal"):
                at = "paid"
            listing["access_type"] = at
            # Non-paid access should behave as active in this MVP.
            if at in ("trial", "free", "partner", "internal"):
                listing["plan_active"] = 1
                listing["paid_status"] = "paid"
                if at == "trial":
                    listing["account_status"] = "trial"
                    if access_expires_at is None and not _date_part(listing.get("access_expires_at")):
                        days = int(get_admin_settings().get("default_trial_days", 0) or 0)
                        if days > 0:
                            listing["access_expires_at"] = _future_date(days)
                elif listing.get("account_status") in ("cancelled", "paused", "archived", "deleted_by_request"):
                    listing["account_status"] = "active"
        if access_expires_at is not None:
            listing["access_expires_at"] = str(access_expires_at or "").strip()
        if access_reason is not None:
            listing["access_reason"] = str(access_reason or "")[:500]
        if feature_overrides is not None:
            allowed_features = {"britesight", "print_promo", "pro_print_kit", "business_coach", "marketing_coach", "masterclass", "accounting", "customer_list"}
            clean_features = {}

            # Backward-compatible input: either a list of feature keys or a dict
            # keyed by feature. The dict supports timed overrides.
            if isinstance(feature_overrides, dict):
                iterable = feature_overrides.items()
            else:
                iterable = [(f, {"enabled": True}) for f in (feature_overrides or [])]

            for f, cfg in iterable:
                ff = str(f or "").strip().lower()
                if ff not in allowed_features:
                    continue
                cfg = cfg if isinstance(cfg, dict) else {"enabled": bool(cfg)}
                clean_features[ff] = {
                    "enabled": bool(cfg.get("enabled", True)),
                    "start": str(cfg.get("start") or cfg.get("start_date") or "").strip()[:10],
                    "end": str(cfg.get("end") or cfg.get("end_date") or "").strip()[:10],
                    "reason": str(cfg.get("reason") or "").strip()[:240],
                }
            listing["feature_overrides"] = clean_features

        listing = _apply_billing_visibility(listing)

        upsert_listing(
            conn,
            listing,
            published=int(listing.get("published", 0)),
            plan=listing.get("plan", "basic"),
            billing=listing.get("billing", "monthly"),
            plan_active=int(listing.get("plan_active", 0)),
            account_status=listing.get("account_status", "active"),
            preview_token=listing.get("preview_token"),
            pending_activation=int(listing.get("pending_activation", 0)),
            requested_at=listing.get("requested_at"),
            activated_at=listing.get("activated_at"),
            admin_note=listing.get("admin_note", ""),
            paid_status=listing.get("paid_status", "unpaid"),
            paid_until=listing.get("paid_until"),
            last_payment_at=listing.get("last_payment_at"),
        )
        conn.commit()
    finally:
        conn.close()

def re_is_postcode(q: str) -> bool:
    # Treat as postcode if starts with digit and has no letters
    s = q.strip()
    if not s:
        return False
    if any(ch.isalpha() for ch in s):
        return False
    return any(ch.isdigit() for ch in s)

# --- Discount codes (admin MVP) -----------------------------------------

def _ensure_discount_codes(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS discount_codes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          code TEXT UNIQUE NOT NULL,
          description TEXT DEFAULT '',
          discount_type TEXT NOT NULL DEFAULT 'percent',
          percent_off REAL,
          amount_off REAL,
          currency TEXT,
          applies_to_plan TEXT DEFAULT 'all',
          billing TEXT DEFAULT 'all',
          max_redemptions INTEGER,
          redemption_count INTEGER NOT NULL DEFAULT 0,
          active INTEGER NOT NULL DEFAULT 1,
          starts_at TEXT,
          ends_at TEXT,
          internal_note TEXT DEFAULT '',
          created_at TEXT DEFAULT (datetime('now')),
          updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_discount_codes_code ON discount_codes(code);
        CREATE INDEX IF NOT EXISTS idx_discount_codes_active ON discount_codes(active);
    """)


def _normalize_discount_code(code: str) -> str:
    raw = str(code or '').strip().upper().replace(' ', '')
    return ''.join(ch for ch in raw if ch.isalnum() or ch in ('-', '_'))[:40]


def _discount_row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    today = date.today().isoformat()
    active = bool(int(row['active'] or 0))
    starts = row['starts_at'] or ''
    ends = row['ends_at'] or ''
    max_red = row['max_redemptions']
    red_count = int(row['redemption_count'] or 0)
    time_ok = (not starts or str(starts) <= today) and (not ends or str(ends) >= today)
    max_ok = max_red is None or int(max_red) <= 0 or red_count < int(max_red)
    usable = active and time_ok and max_ok
    return {
        'id': int(row['id']),
        'code': row['code'],
        'description': row['description'] or '',
        'discount_type': row['discount_type'] or 'percent',
        'percent_off': row['percent_off'],
        'amount_off': row['amount_off'],
        'currency': row['currency'] or '',
        'applies_to_plan': row['applies_to_plan'] or 'all',
        'billing': row['billing'] or 'all',
        'max_redemptions': row['max_redemptions'],
        'redemption_count': red_count,
        'active': active,
        'starts_at': starts,
        'ends_at': ends,
        'internal_note': row['internal_note'] or '',
        'created_at': row['created_at'] or '',
        'updated_at': row['updated_at'] or '',
        'usable_now': usable,
    }


def list_discount_codes(q: str = '', active: str = 'all') -> List[Dict[str, Any]]:
    conn = connect()
    try:
        _ensure_discount_codes(conn)
        where: List[str] = []
        params: List[Any] = []
        if active in ('active', 'inactive'):
            where.append('active=?')
            params.append(1 if active == 'active' else 0)
        qq = (q or '').strip().lower()
        if qq:
            where.append("LOWER(code || ' ' || COALESCE(description,'') || ' ' || COALESCE(internal_note,'')) LIKE ?")
            params.append(f'%{qq}%')
        sql = 'SELECT * FROM discount_codes'
        if where:
            sql += ' WHERE ' + ' AND '.join(where)
        sql += ' ORDER BY active DESC, id DESC'
        return [_discount_row_to_dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def upsert_discount_code(payload: Dict[str, Any], code_id: Optional[int] = None) -> Dict[str, Any]:
    p = payload or {}
    code = _normalize_discount_code(p.get('code') or '')
    if not code:
        raise ValueError('Discount code is required')
    dtype = str(p.get('discount_type') or 'percent').strip().lower()
    if dtype not in ('percent', 'amount'):
        dtype = 'percent'
    percent = None
    amount = None
    if dtype == 'percent':
        try: percent = max(0, min(100, float(p.get('percent_off') or 0)))
        except Exception: percent = 0
        if percent <= 0:
            raise ValueError('Percent discount must be above 0')
    else:
        try: amount = max(0, float(p.get('amount_off') or 0))
        except Exception: amount = 0
        if amount <= 0:
            raise ValueError('Amount discount must be above 0')
    plan = str(p.get('applies_to_plan') or 'all').strip().lower()
    if plan not in ('all','basic','business','growth','pro'):
        plan = 'all'
    billing = str(p.get('billing') or 'all').strip().lower()
    if billing not in ('all','monthly','yearly'):
        billing = 'all'
    max_red = p.get('max_redemptions')
    try:
        max_red = int(max_red) if str(max_red or '').strip() else None
    except Exception:
        max_red = None

    # Currency handling for discount codes:
    # - percent discounts are currency-independent and should not store a currency
    # - fixed-amount discounts must use a known ISO currency code so Stripe checkout can be wired safely later
    allowed_currencies = {'NOK', 'SEK', 'DKK', 'EUR', 'GBP', 'USD', 'CHF'}
    currency = str(p.get('currency') or '').strip().upper()
    if dtype == 'percent':
        currency = ''
    elif currency not in allowed_currencies:
        raise ValueError('Fixed amount discount requires a valid currency: NOK, SEK, DKK, EUR, GBP, USD or CHF')

    conn = connect()
    try:
        _ensure_discount_codes(conn)
        vals = {
            'code': code,
            'description': str(p.get('description') or '')[:240],
            'discount_type': dtype,
            'percent_off': percent,
            'amount_off': amount,
            'currency': currency,
            'applies_to_plan': plan,
            'billing': billing,
            'max_redemptions': max_red,
            'active': 1 if p.get('active', True) else 0,
            'starts_at': str(p.get('starts_at') or '').strip()[:10],
            'ends_at': str(p.get('ends_at') or '').strip()[:10],
            'internal_note': str(p.get('internal_note') or '')[:500],
        }
        if code_id:
            existing = conn.execute('SELECT * FROM discount_codes WHERE id=?', (int(code_id),)).fetchone()
            if not existing:
                raise KeyError('not found')
            conn.execute("""
                UPDATE discount_codes SET
                  code=:code, description=:description, discount_type=:discount_type,
                  percent_off=:percent_off, amount_off=:amount_off, currency=:currency,
                  applies_to_plan=:applies_to_plan, billing=:billing, max_redemptions=:max_redemptions,
                  active=:active, starts_at=:starts_at, ends_at=:ends_at, internal_note=:internal_note,
                  updated_at=datetime('now')
                WHERE id=:id
            """, {**vals, 'id': int(code_id)})
            did = int(code_id)
        else:
            cur = conn.execute("""
                INSERT INTO discount_codes
                  (code, description, discount_type, percent_off, amount_off, currency,
                   applies_to_plan, billing, max_redemptions, active, starts_at, ends_at, internal_note)
                VALUES
                  (:code, :description, :discount_type, :percent_off, :amount_off, :currency,
                   :applies_to_plan, :billing, :max_redemptions, :active, :starts_at, :ends_at, :internal_note)
            """, vals)
            did = int(cur.lastrowid)
        conn.commit()
        row = conn.execute('SELECT * FROM discount_codes WHERE id=?', (did,)).fetchone()
        return _discount_row_to_dict(row)
    except sqlite3.IntegrityError:
        raise ValueError('This discount code already exists')
    finally:
        conn.close()


def set_discount_code_active(code_id: int, active: bool) -> Dict[str, Any]:
    conn = connect()
    try:
        _ensure_discount_codes(conn)
        row = conn.execute('SELECT * FROM discount_codes WHERE id=?', (int(code_id),)).fetchone()
        if not row:
            raise KeyError('not found')
        conn.execute('UPDATE discount_codes SET active=?, updated_at=datetime(\'now\') WHERE id=?', (1 if active else 0, int(code_id)))
        conn.commit()
        row = conn.execute('SELECT * FROM discount_codes WHERE id=?', (int(code_id),)).fetchone()
        return _discount_row_to_dict(row)
    finally:
        conn.close()


# --- Stripe helpers (subscriptions) ---

def get_by_stripe_subscription_id(sub_id: str) -> Optional[Dict[str, Any]]:
    if not sub_id:
        return None
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE stripe_subscription_id=?", (sub_id,)).fetchone()
        return row_to_listing(row) if row else None
    finally:
        conn.close()


def stripe_mark_checkout_session(
    listing_id: int,
    session_id: str,
    price_id: Optional[str] = None,
    status: Optional[str] = None,
) -> None:
    """Store checkout session metadata for troubleshooting."""
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (listing_id,)).fetchone()
        if not row:
            raise KeyError("not found")
        listing = row_to_listing(row)
        listing["stripe_checkout_session_id"] = session_id
        if price_id is not None:
            listing["stripe_price_id"] = price_id
        if status is not None:
            listing["stripe_status"] = status
        listing["stripe_last_event_at"] = conn.execute("SELECT datetime('now') as t").fetchone()["t"]

        listing = _apply_billing_visibility(listing)

        upsert_listing(
            conn,
            listing,
            published=int(listing.get("published", 0)),
            plan=listing.get("plan", "basic"),
            billing=listing.get("billing", "monthly"),
            plan_active=int(listing.get("plan_active", 0)),
            account_status=listing.get("account_status", "active"),
            preview_token=listing.get("preview_token"),
            pending_activation=int(listing.get("pending_activation", 0)),
            requested_at=listing.get("requested_at"),
            activated_at=listing.get("activated_at"),
            admin_note=listing.get("admin_note", ""),
            paid_status=listing.get("paid_status", "unpaid"),
            paid_until=listing.get("paid_until"),
            last_payment_at=listing.get("last_payment_at"),
            stripe_customer_id=listing.get("stripe_customer_id"),
            stripe_subscription_id=listing.get("stripe_subscription_id"),
            stripe_checkout_session_id=listing.get("stripe_checkout_session_id"),
            stripe_status=listing.get("stripe_status"),
            stripe_price_id=listing.get("stripe_price_id"),
            stripe_current_period_end=listing.get("stripe_current_period_end"),
            stripe_last_event_at=listing.get("stripe_last_event_at"),
        )
        conn.commit()
    finally:
        conn.close()



def set_listing_publication(listing_id: int, published: int) -> Dict[str, Any]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (int(listing_id),)).fetchone()
        if not row:
            raise KeyError("not found")
        listing = row_to_listing(row)
        if int(published or 0) == 1 and int(listing.get("plan_active", 0) or 0) != 1:
            raise ValueError("subscription must be active before publishing")
        listing["published"] = 1 if int(published or 0) else 0
        upsert_listing(
            conn,
            listing,
            published=listing["published"],
            plan=listing.get("plan", "basic"),
            billing=listing.get("billing", "monthly"),
            plan_active=int(listing.get("plan_active", 0) or 0),
            preview_token=listing.get("preview_token"),
            pending_activation=int(listing.get("pending_activation", 0) or 0),
            requested_at=listing.get("requested_at"),
            activated_at=listing.get("activated_at"),
        )
        conn.commit()
        return listing
    finally:
        conn.close()

def stripe_mark_subscription_active(
    listing_id: int,
    customer_id: Optional[str],
    subscription_id: Optional[str],
    status: Optional[str],
    current_period_end: Optional[str],
    price_id: Optional[str] = None,
) -> None:
    """Mark listing as paid & active. Publishing remains owner-controlled."""
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE id=?", (listing_id,)).fetchone()
        if not row:
            raise KeyError("not found")
        listing = row_to_listing(row)

        now = conn.execute("SELECT datetime('now') as t").fetchone()["t"]
        activated_at = listing.get("activated_at") or now

        existing_published = int(listing.get("published", 0) or 0)
        listing["published"] = existing_published
        listing["plan_active"] = 1
        listing["pending_activation"] = 0
        listing["paid_status"] = "paid"
        listing["last_payment_at"] = now
        if current_period_end:
            listing["paid_until"] = current_period_end
            listing["stripe_current_period_end"] = current_period_end

        if customer_id:
            listing["stripe_customer_id"] = customer_id
        if subscription_id:
            listing["stripe_subscription_id"] = subscription_id
        if status:
            listing["stripe_status"] = status
        if price_id:
            listing["stripe_price_id"] = price_id
        listing["stripe_last_event_at"] = now

        upsert_listing(
            conn,
            listing,
            published=int(listing.get("published", 0) or 0),
            plan=listing.get("plan", "basic"),
            billing=listing.get("billing", "monthly"),
            plan_active=1,
            preview_token=listing.get("preview_token"),
            pending_activation=0,
            requested_at=listing.get("requested_at"),
            activated_at=activated_at,
            admin_note=listing.get("admin_note", ""),
            paid_status="paid",
            paid_until=listing.get("paid_until"),
            last_payment_at=listing.get("last_payment_at"),
            stripe_customer_id=listing.get("stripe_customer_id"),
            stripe_subscription_id=listing.get("stripe_subscription_id"),
            stripe_checkout_session_id=listing.get("stripe_checkout_session_id"),
            stripe_status=listing.get("stripe_status"),
            stripe_price_id=listing.get("stripe_price_id"),
            stripe_current_period_end=listing.get("stripe_current_period_end"),
            stripe_last_event_at=listing.get("stripe_last_event_at"),
        )
        conn.commit()
    finally:
        conn.close()





# Backward-compatible alias
def stripe_mark_active(*args, **kwargs):
    return stripe_mark_subscription_active(*args, **kwargs)

def stripe_mark_inactive_by_subscription(subscription_id: str, status: Optional[str] = None) -> None:
    """Deactivate listing when subscription is no longer active."""
    if not subscription_id:
        return
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM listings WHERE stripe_subscription_id=?", (subscription_id,)).fetchone()
        if not row:
            return
        listing = row_to_listing(row)
        now = conn.execute("SELECT datetime('now') as t").fetchone()["t"]

        listing["published"] = 0
        listing["plan_active"] = 0
        listing["pending_activation"] = 0
        listing["paid_status"] = "unpaid"
        if status:
            listing["stripe_status"] = status
        listing["stripe_last_event_at"] = now

        upsert_listing(
            conn,
            listing,
            published=0,
            plan=listing.get("plan", "basic"),
            billing=listing.get("billing", "monthly"),
            plan_active=0,
            preview_token=listing.get("preview_token"),
            pending_activation=0,
            requested_at=listing.get("requested_at"),
            activated_at=listing.get("activated_at"),
            admin_note=listing.get("admin_note", ""),
            paid_status="unpaid",
            paid_until=listing.get("paid_until"),
            last_payment_at=listing.get("last_payment_at"),
            stripe_customer_id=listing.get("stripe_customer_id"),
            stripe_subscription_id=listing.get("stripe_subscription_id"),
            stripe_checkout_session_id=listing.get("stripe_checkout_session_id"),
            stripe_status=listing.get("stripe_status"),
            stripe_price_id=listing.get("stripe_price_id"),
            stripe_current_period_end=listing.get("stripe_current_period_end"),
            stripe_last_event_at=listing.get("stripe_last_event_at"),
        )
        conn.commit()
    finally:
        conn.close()



# --- Customers / CRM light (Premium) ---

def customer_row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    try:
        d["tags"] = json.loads(d.get("tags") or "[]")
    except Exception:
        d["tags"] = []
    # Normalize empty strings to None
    for k in ["phone", "email", "notes", "org_no"]:
        if k in d and isinstance(d[k], str) and d[k].strip() == "":
            d[k] = ""
    return d


def list_customers(listing_id: int, q: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = connect()
    try:
        if q:
            qq = f"%{q.strip().lower()}%"
            rows = conn.execute(
                """
                SELECT * FROM customers
                WHERE listing_id=? AND (
                  lower(name) LIKE ? OR lower(phone) LIKE ? OR lower(email) LIKE ? OR lower(notes) LIKE ? OR lower(tags) LIKE ?
                )
                ORDER BY COALESCE(last_contacted_at, updated_at) DESC, id DESC
                """,
                (listing_id, qq, qq, qq, qq, qq),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM customers
                WHERE listing_id=?
                ORDER BY COALESCE(last_contacted_at, updated_at) DESC, id DESC
                """,
                (listing_id,),
            ).fetchall()
        return [customer_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def create_customer(listing_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Name is required")
    phone = (payload.get("phone") or "").strip()
    email = (payload.get("email") or "").strip()
    org_no = (payload.get("org_no") or "").strip()
    notes = (payload.get("notes") or "").strip()

    tags = payload.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    if not isinstance(tags, list):
        tags = []
    tags_json = json.dumps(tags, ensure_ascii=False)

    last_contacted_at = (payload.get("last_contacted_at") or "").strip() or None

    def _next_customer_no(conn: sqlite3.Connection, lid: int) -> str:
        rows = conn.execute("SELECT customer_no FROM customers WHERE listing_id=?", (lid,)).fetchall()
        max_n = 0
        for r in rows:
            cn = (r[0] if not isinstance(r, sqlite3.Row) else r["customer_no"]) or ""
            if isinstance(cn, str) and cn.startswith("C-"):
                try:
                    max_n = max(max_n, int(cn.split("-", 1)[1]))
                except Exception:
                    pass
        return f"C-{(max_n + 1):04d}"

    conn = connect()
    try:
        customer_no = _next_customer_no(conn, listing_id)
        cur = conn.execute(
            """
            INSERT INTO customers(listing_id,customer_no,org_no,name,phone,email,tags,notes,last_contacted_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (listing_id, customer_no, org_no, name, phone, email, tags_json, notes, last_contacted_at),
        )
        cid = int(cur.lastrowid)
        conn.commit()
        row = conn.execute("SELECT * FROM customers WHERE id=? AND listing_id=?", (cid, listing_id)).fetchone()
        return customer_row_to_dict(row)
    finally:
        conn.close()


def update_customer(listing_id: int, customer_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM customers WHERE id=? AND listing_id=?", (customer_id, listing_id)).fetchone()
        if not row:
            raise ValueError("Customer not found")

        name = (payload.get("name") if "name" in payload else row["name"]) or ""
        name = name.strip()
        if not name:
            raise ValueError("Name is required")

        phone = (payload.get("phone") if "phone" in payload else row["phone"]) or ""
        email = (payload.get("email") if "email" in payload else row["email"]) or ""

        org_no = (payload.get("org_no") if "org_no" in payload else row["org_no"]) or ""
        notes = (payload.get("notes") if "notes" in payload else row["notes"]) or ""

        tags = payload.get("tags") if "tags" in payload else row["tags"]
        if isinstance(tags, str):
            # could be json or comma list
            try:
                maybe = json.loads(tags)
                if isinstance(maybe, list):
                    tags = maybe
                else:
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
            except Exception:
                tags = [t.strip() for t in tags.split(",") if t.strip()]
        if isinstance(tags, list):
            tags_json = json.dumps([str(t).strip() for t in tags if str(t).strip()], ensure_ascii=False)
        else:
            tags_json = row["tags"]

        last_contacted_at = payload.get("last_contacted_at") if "last_contacted_at" in payload else row["last_contacted_at"]
        if isinstance(last_contacted_at, str) and last_contacted_at.strip()=="":
            last_contacted_at = None

        conn.execute(
            """
            UPDATE customers
            SET name=?, org_no=?, phone=?, email=?, tags=?, notes=?, last_contacted_at=?, updated_at=datetime('now')
            WHERE id=? AND listing_id=?
            """,
            (name, org_no.strip(), phone.strip(), email.strip(), tags_json, notes.strip(), last_contacted_at, customer_id, listing_id),
        )
        conn.commit()
        row2 = conn.execute("SELECT * FROM customers WHERE id=? AND listing_id=?", (customer_id, listing_id)).fetchone()
        return customer_row_to_dict(row2)
    finally:
        conn.close()


def delete_customer(listing_id: int, customer_id: int) -> bool:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM customers WHERE id=? AND listing_id=?", (customer_id, listing_id))
        conn.commit()
        return (cur.rowcount or 0) > 0
    finally:
        conn.close()



# --- Accounting (mini ledger) ---
def tx_row_to_dict(row):
    d = dict(row)
    raw_items = d.get("items_json")
    items = None
    if raw_items:
        try:
            items = json.loads(raw_items)
        except Exception:
            items = None
    return {
        "id": int(d.get("id")),
        "date": d.get("tx_date") or "",
        "type": d.get("tx_type") or "",
        "customer_id": (int(d.get("customer_id")) if d.get("customer_id") is not None else None),
        "dish_name": (d.get("dish_name") or ""),
        "qty": (int(d.get("qty")) if d.get("qty") is not None else 1),
        "category": d.get("category") or "",
        "amount": float(d.get("amount") or 0),
        "currency": d.get("currency") or "",
        "note": d.get("note") or "",
        "items": items,
        "created_at": d.get("created_at") or "",
    }



def list_transactions(listing_id: int,
                      date_from: Optional[str] = None,
                      date_to: Optional[str] = None,
                      tx_type: Optional[str] = None,
                      q: Optional[str] = None,
                      category: Optional[str] = None,
                      limit: int = 200,
                      offset: int = 0):
    conn = connect()
    try:
        where = ["listing_id = ?"]
        params = [listing_id]
        if date_from:
            where.append("tx_date >= ?")
            params.append(date_from)
        if date_to:
            where.append("tx_date <= ?")
            params.append(date_to)
        if tx_type and tx_type in ("income", "expense"):
            where.append("tx_type = ?")
            params.append(tx_type)
        if category:
            where.append("lower(category) = lower(?)")
            params.append(category)
        if q:
            like = f"%{q.strip().lower()}%"
            where.append("(lower(category) LIKE ? OR lower(note) LIKE ? OR lower(COALESCE(dish_name,'')) LIKE ?)")
            params.extend([like, like, like])

        sql = "SELECT * FROM accounting_transactions WHERE " + " AND ".join(where) + " ORDER BY tx_date DESC, id DESC LIMIT ? OFFSET ?"
        params2 = params + [limit, offset]
        rows = conn.execute(sql, params2).fetchall()

        count_sql = "SELECT COUNT(*) AS c FROM accounting_transactions WHERE " + " AND ".join(where)
        count = conn.execute(count_sql, params).fetchone()["c"]

        items = [tx_row_to_dict(r) for r in rows]

        # Attach receipt info (if any)
        try:
            ids = [int(it.get('id')) for it in items if it.get('id') is not None]
            if ids:
                qmarks = ','.join(['?'] * len(ids))
                rrows = conn.execute(
                    f"SELECT id, transaction_id, receipt_no, public_token, status FROM receipts "
                    f"WHERE listing_id=? AND transaction_id IN ({qmarks}) AND (status IS NULL OR status!='replaced') "
                    f"ORDER BY id DESC",
                    [listing_id] + ids,
                ).fetchall()
                rmap = {}
                for r in rrows:
                    txid = int(r['transaction_id'])
                    if txid not in rmap:
                        rmap[txid] = dict(r)
                for it in items:
                    rid = rmap.get(int(it['id'])) if it.get('id') is not None else None
                    if rid:
                        it['receipt_id'] = int(rid.get('id'))
                        it['receipt_no'] = rid.get('receipt_no') or ''
                        it['receipt_public_token'] = rid.get('public_token') or ''
                        it['receipt_status'] = rid.get('status') or 'issued'
                    else:
                        it['receipt_id'] = None
                        it['receipt_no'] = ''
                        it['receipt_public_token'] = ''
                        it['receipt_status'] = ''
        except Exception:

            for it in items:
                it['receipt_id'] = None
                it['receipt_no'] = ''
                it['receipt_public_token'] = ''

        return items, int(count)
    finally:
        conn.close()


def top_customers(listing_id: int,
                  date_from: Optional[str] = None,
                  date_to: Optional[str] = None,
                  limit: int = 10) -> List[Dict[str, Any]]:
    """Summarize income per customer (only rows with customer_id)."""
    conn = connect()
    try:
        where = ["t.listing_id = ?", "t.tx_type='income'", "t.customer_id IS NOT NULL"]
        params: List[Any] = [listing_id]
        if date_from:
            where.append("t.tx_date >= ?")
            params.append(date_from)
        if date_to:
            where.append("t.tx_date <= ?")
            params.append(date_to)
        sql = (
            "SELECT c.id as customer_id, c.customer_no, c.name, SUM(t.amount) as total "
            "FROM accounting_transactions t "
            "JOIN customers c ON c.id = t.customer_id "
            "WHERE " + " AND ".join(where) +
            " GROUP BY c.id, c.customer_no, c.name "
            "ORDER BY total DESC, c.name ASC "
            "LIMIT ?"
        )
        rows = conn.execute(sql, params + [int(limit or 10)]).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            out.append({
                "customer_id": int(d.get("customer_id")),
                "customer_no": d.get("customer_no") or "",
                "name": d.get("name") or "",
                "total": float(d.get("total") or 0),
            })
        return out
    finally:
        conn.close()



def top_dishes(listing_id: int,
               date_from: Optional[str] = None,
               date_to: Optional[str] = None,
               limit: int = 10) -> List[Dict[str, Any]]:
    """Summarize income per dish/item.

    MVP notes:
    - If `dish_name` is present, we count it.
    - If `items_json` is present (receipt-like line items), we also count each item name.
      We apportion the transaction amount across items by qty share (simple heuristic).
    """
    conn = connect()
    try:
        where = ["listing_id = ?", "tx_type='income'"]
        params: List[Any] = [listing_id]
        if date_from:
            where.append("tx_date >= ?")
            params.append(date_from)
        if date_to:
            where.append("tx_date <= ?")
            params.append(date_to)

        # Pull the minimal fields needed for aggregation.
        rows = conn.execute(
            "SELECT dish_name, COALESCE(qty,1) as qty, amount, items_json "
            "FROM accounting_transactions "
            "WHERE " + " AND ".join(where),
            params,
        ).fetchall()

        # Aggregate by item name.
        agg_amt: Dict[str, float] = {}
        agg_qty: Dict[str, int] = {}

        def add(name: str, amt: float, q: int):
            n = (name or '').strip()
            if not n:
                return
            agg_amt[n] = float(agg_amt.get(n, 0.0)) + float(amt or 0.0)
            agg_qty[n] = int(agg_qty.get(n, 0)) + int(q or 0)

        for r in rows:
            d = dict(r)
            dish_name = (d.get("dish_name") or "").strip()
            qty = int(d.get("qty") or 1)
            if qty <= 0:
                qty = 1
            amount = float(d.get("amount") or 0.0)
            items_json = d.get("items_json")

            # Prefer detailed line items if present; otherwise fall back to dish_name.
            parsed_items: List[Dict[str, Any]] = []
            if items_json:
                try:
                    parsed = json.loads(items_json) if isinstance(items_json, str) else items_json
                    if isinstance(parsed, list):
                        for it in parsed:
                            if not isinstance(it, dict):
                                continue
                            nm = str(it.get("name") or "").strip()
                            if not nm:
                                continue
                            try:
                                q = int(it.get("qty") or 1)
                            except Exception:
                                q = 1
                            if q <= 0:
                                q = 1
                            parsed_items.append({"name": nm, "qty": q})
                except Exception:
                    parsed_items = []

            if parsed_items:
                total_q = sum(int(it.get("qty") or 1) for it in parsed_items) or 1
                # Apportion the transaction amount across items by qty share.
                for it in parsed_items:
                    q = int(it.get("qty") or 1)
                    share = amount * (q / total_q)
                    add(it.get("name") or "", share, q)
            elif dish_name:
                add(dish_name, amount, qty)

        # Build result list
        out = [{
            "dish_name": name,
            "total_amount": float(agg_amt.get(name) or 0.0),
            "total_qty": int(agg_qty.get(name) or 0),
        } for name in agg_amt.keys()]

        out.sort(key=lambda x: (-float(x.get("total_amount") or 0.0), -int(x.get("total_qty") or 0), str(x.get("dish_name") or "").lower()))
        return out[:int(limit or 10)]
    finally:
        conn.close()



def get_transaction_by_id(listing_id: int, tx_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT * FROM accounting_transactions WHERE id=? AND listing_id=?",
            (int(tx_id), int(listing_id)),
        ).fetchone()
        return tx_row_to_dict(row) if row else None
    finally:
        conn.close()

def create_transaction(listing_id: int, payload: Dict[str, Any], default_currency: str = "") -> Dict[str, Any]:
    tx_type = str(payload.get("type") or "").strip().lower()
    if tx_type not in ("income", "expense"):
        raise ValueError("type must be income or expense")
    try:
        amount = float(payload.get("amount") or 0)
    except Exception:
        amount = 0
    if amount <= 0:
        raise ValueError("amount must be > 0")

    tx_date = str(payload.get("date") or "").strip()
    if not tx_date:
        tx_date = datetime.utcnow().strftime("%Y-%m-%d")

    category = str(payload.get("category") or "").strip()
    note = str(payload.get("note") or "").strip()
    # MVP best practice: currency is per listing (settings), not per transaction.
    currency = str(default_currency or "").strip()

    # Optional customer link (income only)
    customer_id = payload.get("customer_id") if tx_type == "income" else None
    if customer_id in ("", 0, "0"):
        customer_id = None
    if customer_id is not None:
        try:
            customer_id = int(customer_id)
        except Exception:
            raise ValueError("customer_id must be an integer")

    # Optional dish / quantity (income only)
    dish_name = ""
    qty = 1
    if tx_type == "income":
        dish_name = str(payload.get("dish_name") or payload.get("dish") or "").strip()
        qv = payload.get("qty")
        if qv in (None, ""):
            qty = 1
        else:
            try:
                qty = int(qv)
            except Exception:
                raise ValueError("qty must be an integer")
        if qty <= 0:
            raise ValueError("qty must be >= 1")
        if qty > 9999:
            qty = 9999
        # Avoid storing extremely long labels
        if len(dish_name) > 120:
            dish_name = dish_name[:120]

    # Optional structured line items (json array). Stored as TEXT in SQLite.
    items_json: Optional[str] = None
    raw_items = payload.get("items")
    if raw_items is None:
        raw_items = payload.get("items_json")
    if raw_items not in (None, ""):
        try:
            # Accept either list/dict (from JSON) or string (already serialized).
            if isinstance(raw_items, str):
                parsed = json.loads(raw_items)
            else:
                parsed = raw_items
            if not isinstance(parsed, list):
                raise ValueError("items_json must be a JSON array")
            # Clamp size for MVP safety
            if len(parsed) > 60:
                parsed = parsed[:60]
            clean: List[Dict[str, Any]] = []
            for it in parsed:
                if not isinstance(it, dict):
                    continue
                name = str(it.get("name") or "").strip()
                if not name:
                    continue
                kind = str(it.get("kind") or it.get("type") or "").strip().lower() or "main"
                if kind not in ("main", "side", "other", "sale"):
                    kind = "main"
                try:
                    q = int(it.get("qty") or 1)
                except Exception:
                    q = 1
                if q <= 0:
                    q = 1
                if q > 9999:
                    q = 9999
                up = it.get("unit_price")
                if up in (None, ""):
                    unit_price = None
                else:
                    try:
                        unit_price = float(up)
                    except Exception:
                        unit_price = None
                clean.append({
                    "name": name[:120],
                    "kind": kind,
                    "qty": q,
                    "unit_price": unit_price,
                })
            items_json = json.dumps(clean, ensure_ascii=False)
        except Exception:
            # If items parsing fails, ignore (do not block transaction creation in MVP)
            items_json = None

    conn = connect()
    try:
        if customer_id is not None:
            exists = conn.execute(
                "SELECT id FROM customers WHERE id=? AND listing_id=?",
                (customer_id, listing_id),
            ).fetchone()
            if not exists:
                raise ValueError("Customer not found")
        cur = conn.execute(
            """
            INSERT INTO accounting_transactions(listing_id, tx_date, tx_type, customer_id, dish_name, qty, items_json, category, amount, currency, note, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?, ?, datetime('now'), datetime('now'))
            """,
            (listing_id, tx_date, tx_type, customer_id, (dish_name or None), int(qty or 1), items_json, category, amount, currency, note),
        )
        tid = int(cur.lastrowid)
        conn.commit()
        row = conn.execute("SELECT * FROM accounting_transactions WHERE id=? AND listing_id=?", (tid, listing_id)).fetchone()
        return tx_row_to_dict(row)
    finally:
        conn.close()


def delete_transaction(listing_id: int, tx_id: int) -> bool:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM accounting_transactions WHERE id=? AND listing_id=?", (tx_id, listing_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def summarize_transactions(items: List[Dict[str, Any]]):
    inc = 0.0
    exp = 0.0
    for it in items:
        if it.get("type") == "income":
            inc += float(it.get("amount") or 0)
        elif it.get("type") == "expense":
            exp += float(it.get("amount") or 0)
    return {"income": round(inc, 2), "expense": round(exp, 2), "net": round(inc - exp, 2)}


# --- Receipts (offline-friendly sales docs) ---

def receipt_row_to_dict(row):
    d = dict(row)
    return {
        "id": int(d.get("id")),
        "listing_id": int(d.get("listing_id")),
        "transaction_id": (int(d.get("transaction_id")) if d.get("transaction_id") is not None else None),
        "receipt_no": d.get("receipt_no") or "",
        "public_token": d.get("public_token") or "",
        "doc_type": d.get("doc_type") or "receipt",
        "issue_date": d.get("issue_date") or "",
        "due_date": d.get("due_date") or "",
        "paid": int(d.get("paid") or 0),
        "paid_date": d.get("paid_date") or "",
        "payment_method": d.get("payment_method") or "",
        "buyer_name": d.get("buyer_name") or "",
        "buyer_org_no": d.get("buyer_org_no") or "",
        "buyer_email": d.get("buyer_email") or "",
        "buyer_phone": d.get("buyer_phone") or "",
        "buyer_ref": d.get("buyer_ref") or "",
        "description": d.get("description") or "",
        "items_json": d.get("items_json") or "",
        "amount": float(d.get("amount") or 0),
        "currency": d.get("currency") or "",
        "note": d.get("note") or "",
        "status": d.get("status") or "issued",
        "replaces_receipt_id": (int(d.get("replaces_receipt_id")) if d.get("replaces_receipt_id") is not None else None),
        "email_last_to": d.get("email_last_to") or "",
        "email_sent_at": d.get("email_sent_at") or "",
        "email_status": d.get("email_status") or "",
        "email_error": d.get("email_error") or "",
        "created_at": d.get("created_at") or "",
        "updated_at": d.get("updated_at") or "",
    }


def _next_receipt_no(conn: sqlite3.Connection, listing_id: int, year: int) -> str:
    prefix = f"R-{year}-"
    rows = conn.execute(
        "SELECT receipt_no FROM receipts WHERE listing_id=? AND receipt_no LIKE ? ORDER BY id DESC LIMIT 200",
        (listing_id, prefix + "%"),
    ).fetchall()
    max_n = 0
    for r in rows:
        rn = (r[0] if not isinstance(r, sqlite3.Row) else r["receipt_no"]) or ""
        if isinstance(rn, str) and rn.startswith(prefix):
            try:
                n = int(rn.split(prefix, 1)[1])
                if n > max_n:
                    max_n = n
            except Exception:
                pass
    return f"{prefix}{max_n+1:04d}"


def create_receipt(listing_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a receipt/invoice document (offline payment friendly).

    For MVP, this is created from an income transaction.
    """
    tx_id = payload.get("transaction_id")
    if tx_id in (None, ""):
        raise ValueError("transaction_id is required")
    try:
        tx_id = int(tx_id)
    except Exception:
        raise ValueError("transaction_id must be an integer")

    doc_type = str(payload.get("doc_type") or "receipt").strip().lower()
    if doc_type not in ("receipt", "invoice"):
        doc_type = "receipt"

    issue_date = str(payload.get("issue_date") or "").strip()
    due_date = str(payload.get("due_date") or "").strip() or None

    buyer_name = str(payload.get("buyer_name") or "").strip()
    buyer_org_no = str(payload.get("buyer_org_no") or "").strip()
    buyer_email = str(payload.get("buyer_email") or "").strip()
    buyer_phone = str(payload.get("buyer_phone") or "").strip()
    buyer_ref = str(payload.get("buyer_ref") or "").strip()

    payment_method = str(payload.get("payment_method") or "").strip()
    note = str(payload.get("note") or "").strip()

    # Optional structured "what was purchased" fields.
    # We store these on the underlying income transaction (not on the receipt)
    # so the accounting insights ("best selling dishes") stay consistent even
    # when receipts are created later.
    dish_name_in = payload.get("dish_name", None)
    qty_in = payload.get("qty", None)

    paid = int(payload.get("paid") if payload.get("paid") is not None else 1)
    paid = 1 if paid else 0
    paid_date = str(payload.get("paid_date") or "").strip() or None

    force_new = int(payload.get("force_new") or 0)
    force_new = 1 if force_new else 0

    conn = connect()
    try:
        # Load transaction
        tx = conn.execute(
            "SELECT * FROM accounting_transactions WHERE id=? AND listing_id=?",
            (tx_id, listing_id),
        ).fetchone()
        if not tx:
            raise ValueError("Transaction not found")
        if (tx["tx_type"] if isinstance(tx, sqlite3.Row) else tx[3]) != "income":
            raise ValueError("Receipt can only be created for income")

        tx_date = tx["tx_date"] if isinstance(tx, sqlite3.Row) else tx[2]
        amount = float(tx["amount"] if isinstance(tx, sqlite3.Row) else tx[8])
        category = (tx["category"] if isinstance(tx, sqlite3.Row) else tx[7]) or "Sales"
        tx_note = (tx["note"] if isinstance(tx, sqlite3.Row) else tx[10]) or ""
        currency = (tx["currency"] if isinstance(tx, sqlite3.Row) else tx[9]) or ""
        tx_items_json = (tx['items_json'] if isinstance(tx, sqlite3.Row) else (tx[7] if len(tx)>7 else None))

        # If a receipt already exists for this transaction, default to returning it.

        # Optional: update dish_name/qty on the underlying transaction when provided.
        # This lets owners backfill "what was purchased" when they generate a receipt.
        if (dish_name_in is not None) or (qty_in is not None):
            dish_name_val = None
            if dish_name_in is not None:
                dn = str(dish_name_in or "").strip()
                dish_name_val = dn if dn else None
            else:
                # keep current
                dish_name_val = (tx["dish_name"] if isinstance(tx, sqlite3.Row) else tx[5])

            qty_val = None
            if qty_in is not None:
                try:
                    qv = int(qty_in)
                except Exception:
                    qv = 1
                if qv <= 0:
                    qv = 1
                qty_val = qv
            else:
                qty_val = (tx["qty"] if isinstance(tx, sqlite3.Row) else tx[6])
                try:
                    qty_val = int(qty_val) if qty_val is not None else 1
                except Exception:
                    qty_val = 1

            conn.execute(
                "UPDATE accounting_transactions SET dish_name=?, qty=?, updated_at=datetime('now') WHERE id=? AND listing_id=?",
                (dish_name_val, qty_val, int(tx_id), int(listing_id)),
            )
            conn.commit()
            # refresh tx for downstream defaults
            tx = conn.execute(
                "SELECT * FROM accounting_transactions WHERE id=? AND listing_id=?",
                (tx_id, listing_id),
            ).fetchone()
        # If force_new=1, we create a replacement receipt and mark the previous one as replaced.
        existing = conn.execute(
            "SELECT * FROM receipts WHERE listing_id=? AND transaction_id=? AND (status IS NULL OR status!='replaced') ORDER BY id DESC LIMIT 1",
            (listing_id, tx_id),
        ).fetchone()

        replaces_receipt_id = None
        if existing and not force_new:
            return receipt_row_to_dict(existing)
        if existing and force_new:
            replaces_receipt_id = int(existing["id"]) if isinstance(existing, sqlite3.Row) else int(existing[0])
            conn.execute(
                "UPDATE receipts SET status='replaced', updated_at=datetime('now') WHERE id=? AND listing_id=?",
                (replaces_receipt_id, listing_id),
            )

        if not issue_date:
            issue_date = str(tx_date or datetime.utcnow().strftime("%Y-%m-%d"))

        year = int(issue_date.split("-", 1)[0]) if "-" in issue_date else datetime.utcnow().year
        receipt_no = _next_receipt_no(conn, listing_id, year)

        import secrets
        public_token = secrets.token_urlsafe(16)

        # Description (free-text). If not provided, build a useful default.
        description = str(payload.get("description") or "").strip()
        if not description:
            tx_dish = (tx["dish_name"] if isinstance(tx, sqlite3.Row) else tx[5]) or ""
            tx_qty = (tx["qty"] if isinstance(tx, sqlite3.Row) else tx[6])
            try:
                tx_qty = int(tx_qty) if tx_qty is not None else 1
            except Exception:
                tx_qty = 1
            tx_dish = str(tx_dish or "").strip()
            if tx_dish:
                description = f"{tx_dish} x{max(tx_qty,1)}"
            else:
                description = (category or "Sales")
        # If note is empty, default to tx_note
        if not note and tx_note:
            note = str(tx_note).strip()

        if paid and not paid_date:
            paid_date = issue_date

        # Copy line items from payload or underlying transaction (if available)
        receipt_items_json = None
        raw_items2 = payload.get('items')
        if raw_items2 is None:
            raw_items2 = payload.get('items_json')
        if raw_items2 not in (None, ''):
            try:
                if isinstance(raw_items2, str):
                    parsed2 = json.loads(raw_items2)
                else:
                    parsed2 = raw_items2
                if isinstance(parsed2, list):
                    receipt_items_json = json.dumps(parsed2, ensure_ascii=False)
            except Exception:
                receipt_items_json = None
        if receipt_items_json is None and tx_items_json:
            receipt_items_json = str(tx_items_json)

        cur = conn.execute(
            """
            INSERT INTO receipts(
              listing_id, transaction_id, receipt_no, public_token,
              doc_type, issue_date, due_date, paid, paid_date, payment_method,
              buyer_name, buyer_org_no, buyer_email, buyer_phone, buyer_ref,
              description, items_json, amount, currency, note, status, replaces_receipt_id,
              created_at, updated_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, datetime('now'), datetime('now'))
            """,
            (
                listing_id,
                tx_id,
                receipt_no,
                public_token,
                doc_type,
                issue_date,
                due_date,
                paid,
                paid_date,
                payment_method,
                buyer_name,
                buyer_org_no,
                buyer_email,
                buyer_phone,
                buyer_ref,
                description,
                receipt_items_json,
                amount,
                currency,
                note,
                'issued',
                replaces_receipt_id,
            ),
        )
        rid = int(cur.lastrowid)
        conn.commit()
        row = conn.execute("SELECT * FROM receipts WHERE id=? AND listing_id=?", (rid, listing_id)).fetchone()
        return receipt_row_to_dict(row)
    finally:
        conn.close()


def list_receipts(listing_id: int,
                  date_from: Optional[str] = None,
                  date_to: Optional[str] = None,
                  q: Optional[str] = None,
                  include_replaced: bool = False,
                  limit: int = 100,
                  offset: int = 0):
    conn = connect()
    try:
        where = ["listing_id = ?"]
        params: List[Any] = [listing_id]
        if not include_replaced:
            where.append("(status IS NULL OR status!='replaced')")
        if date_from:
            where.append("issue_date >= ?")
            params.append(date_from)
        if date_to:
            where.append("issue_date <= ?")
            params.append(date_to)
        if q:
            like = f"%{q.strip().lower()}%"
            where.append("(lower(receipt_no) LIKE ? OR lower(buyer_name) LIKE ? OR lower(buyer_email) LIKE ?)")
            params.extend([like, like, like])

        sql = "SELECT * FROM receipts WHERE " + " AND ".join(where) + " ORDER BY issue_date DESC, id DESC LIMIT ? OFFSET ?"
        rows = conn.execute(sql, params + [limit, offset]).fetchall()
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM receipts WHERE " + " AND ".join(where),
            params,
        ).fetchone()["c"]
        items = [receipt_row_to_dict(r) for r in rows]
        return items, int(count)
    finally:
        conn.close()


def get_receipt_by_id(listing_id: int, receipt_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM receipts WHERE id=? AND listing_id=?", (int(receipt_id), int(listing_id))).fetchone()
        return receipt_row_to_dict(row) if row else None
    finally:
        conn.close()


def get_receipt_by_public_token(public_token: str) -> Optional[Dict[str, Any]]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM receipts WHERE public_token=?", (public_token,)).fetchone()
        return receipt_row_to_dict(row) if row else None
    finally:
        conn.close()


def set_receipt_email_status(listing_id: int, receipt_id: int, email_to: str, status: str, error: str = '') -> Optional[Dict[str, Any]]:
    # Update email status fields for a receipt and return the updated row.
    conn = connect()
    try:
        email_to = str(email_to or '').strip()
        status = str(status or '').strip()
        error = str(error or '').strip()
        # Only set sent_at when status == 'sent'
        if status == 'sent':
            conn.execute(
                "UPDATE receipts SET email_last_to=?, email_sent_at=datetime('now'), email_status=?, email_error=?, updated_at=datetime('now') WHERE id=? AND listing_id=?",
                (email_to, status, error, int(receipt_id), int(listing_id)),
            )
        else:
            conn.execute(
                "UPDATE receipts SET email_last_to=?, email_status=?, email_error=?, updated_at=datetime('now') WHERE id=? AND listing_id=?",
                (email_to, status, error, int(receipt_id), int(listing_id)),
            )
        conn.commit()
        row = conn.execute("SELECT * FROM receipts WHERE id=? AND listing_id=?", (int(receipt_id), int(listing_id))).fetchone()
        return receipt_row_to_dict(row) if row else None
    finally:
        conn.close()
