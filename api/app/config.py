from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

_VALID_ENVS = {"development", "staging", "production"}


def _normalize_env(value: str | None) -> str:
    raw = (value or "development").strip().lower()
    if raw in {"dev", "local"}:
        raw = "development"
    if raw in {"prod", "live"}:
        raw = "production"
    if raw not in _VALID_ENVS:
        raise RuntimeError(
            f"Invalid RICEMAP_ENV={value!r}. Use development, staging or production."
        )
    return raw


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _csv_env(name: str, default: str = "") -> List[str]:
    raw = os.environ.get(name, default)
    return [p.strip() for p in raw.split(",") if p.strip()]


@dataclass(frozen=True)
class RuntimeConfig:
    env: str
    debug: bool
    admin_key: str
    session_secret: str
    cors_allowed_origins: List[str]
    enable_demo_seed: bool
    enable_legacy_admin_key: bool
    allow_unsafe_production: bool
    data_dir: str
    code_dir: str
    database_url: str
    database_engine: str
    database_path: str
    database_ssl: bool
    session_days: int
    login_max_failed_attempts: int
    login_lockout_minutes: int
    upload_storage_mode: str
    uploads_dir: str
    upload_max_mb: int
    public_base_url: str
    require_https: bool
    backup_configured: bool
    backup_dir: str
    backup_uploads_enabled: bool
    error_monitoring_configured: bool
    error_log_configured: bool
    request_logging_enabled: bool
    log_level: str
    error_log_retention_days: int
    stripe_mode: str
    deployment_provider: str
    deployment_region: str
    release_version: str
    git_commit_sha: str
    port: int

    @property
    def is_development(self) -> bool:
        return self.env == "development"

    @property
    def is_staging(self) -> bool:
        return self.env == "staging"

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def allow_demo_seed(self) -> bool:
        # Demo/test kitchens must be explicit outside local development.
        # Production never auto-seeds demo data.
        return (not self.is_production) and bool(self.enable_demo_seed)

    @property
    def legacy_admin_key_available(self) -> bool:
        # Session login is the normal admin path. The old key fallback is only
        # for local development unless explicitly enabled outside production.
        return (not self.is_production) and bool(self.enable_legacy_admin_key and self.admin_key)

    @property
    def safe_cors_origins(self) -> List[str]:
        if self.is_development:
            return self.cors_allowed_origins or ["*"]
        return self.cors_allowed_origins

    @property
    def persistent_data_dir_set(self) -> bool:
        return bool(self.data_dir)

    @property
    def database_inside_code_dir(self) -> bool:
        if self.database_engine != "sqlite" or not self.database_path:
            return False
        return _path_is_inside(self.database_path, self.code_dir)

    @property
    def uploads_inside_code_dir(self) -> bool:
        return _path_is_inside(self.uploads_dir, self.code_dir) if self.uploads_dir else False

    @property
    def backup_inside_code_dir(self) -> bool:
        return _path_is_inside(self.backup_dir, self.code_dir) if self.backup_dir else False

    @property
    def user_data_outside_code_dir(self) -> bool:
        if not self.persistent_data_dir_set:
            return False
        db_ok = True if self.database_engine != "sqlite" else bool(self.database_path and not self.database_inside_code_dir)
        uploads_ok = bool(self.uploads_dir and not self.uploads_inside_code_dir)
        backups_ok = bool(self.backup_dir and not self.backup_inside_code_dir)
        return bool(db_ok and uploads_ok and backups_ok)


def _code_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _path_is_inside(path_value: str, parent_value: str) -> bool:
    if not path_value or not parent_value:
        return False
    try:
        Path(path_value).resolve().relative_to(Path(parent_value).resolve())
        return True
    except Exception:
        return False


def _sqlite_url_from_path(path: Path) -> str:
    return f"sqlite:///{path.resolve()}"


def _default_sqlite_url(data_dir: Path | None = None) -> str:
    base = data_dir if data_dir else _code_root()
    return _sqlite_url_from_path(base / "ricemap24.sqlite3")


def _clean_database_url(database_url: str) -> str:
    raw = (database_url or "").strip().strip('\"').strip("'").strip()
    if not raw:
        return ""

    # Render's database connection UI can show either a bare URL or a shell
    # command containing the URL. Accept both to avoid deploy failures caused by
    # harmless formatting around the actual connection string.
    match = re.search(r"(postgresql|postgres|sqlite)://[^\s'\"]+", raw, flags=re.IGNORECASE)
    if match:
        raw = match.group(0)

    # psycopg and the rest of the app use the standard postgresql:// spelling.
    # Render may provide postgres://, so normalize it here.
    if raw.lower().startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://"):]
    return raw


def _database_engine(database_url: str) -> str:
    raw = _clean_database_url(database_url).lower()
    if not raw:
        return 'sqlite'
    if raw.startswith('sqlite:///') or raw.startswith('sqlite:////'):
        return 'sqlite'
    if raw.startswith('postgresql://'):
        return 'postgresql'
    raise RuntimeError('Unsupported DATABASE_URL. Use sqlite:///... for local development or postgresql://... for staging/production.')


def _sqlite_path_from_url(database_url: str) -> str:
    if not database_url:
        return str((_code_root() / 'ricemap24.sqlite3').resolve())
    raw = database_url.strip()
    if raw.startswith('sqlite:///'):
        # sqlite:////absolute/path.db -> /absolute/path.db
        # sqlite:///relative/path.db -> relative/path.db from project root
        body = raw[len('sqlite:///'):]
        if body.startswith('/'):
            return str(Path(body).resolve())
        return str((_code_root() / body).resolve())
    return ''

def load_runtime_config() -> RuntimeConfig:
    env = _normalize_env(os.environ.get("RICEMAP_ENV"))
    is_dev = env == "development"
    is_prod = env == "production"
    code_dir = _code_root()
    raw_data_dir = (os.environ.get("RICEMAP_DATA_DIR", "") or "").strip()
    data_dir = Path(raw_data_dir).expanduser().resolve() if raw_data_dir else None
    database_url = _clean_database_url(os.environ.get("DATABASE_URL", "")) or _default_sqlite_url(data_dir)
    database_engine = _database_engine(database_url)
    database_path = _sqlite_path_from_url(database_url) if database_engine == "sqlite" else ""
    uploads_default = (data_dir / "uploads") if data_dir else (code_dir / "uploads")
    backup_default = (data_dir / "backups") if data_dir else (code_dir / "backups")
    cfg = RuntimeConfig(
        env=env,
        debug=_truthy(os.environ.get("RICEMAP_DEBUG", "1" if is_dev else "0")),
        admin_key=os.environ.get("RICEMAP_ADMIN_KEY", "admin" if is_dev else ""),
        session_secret=os.environ.get("RICEMAP_SESSION_SECRET", ""),
        cors_allowed_origins=_csv_env("CORS_ALLOWED_ORIGINS"),
        enable_demo_seed=_truthy(os.environ.get("ENABLE_DEMO_SEED", "1" if is_dev else "0")),
        enable_legacy_admin_key=_truthy(os.environ.get("RICEMAP_ENABLE_LEGACY_ADMIN_KEY", "1" if is_dev else "0")),
        allow_unsafe_production=_truthy(os.environ.get("RICEMAP_ALLOW_UNSAFE_PRODUCTION")),
        data_dir=str(data_dir) if data_dir else "",
        code_dir=str(code_dir),
        database_url=database_url,
        database_engine=database_engine,
        database_path=database_path,
        database_ssl=_truthy(os.environ.get("DATABASE_SSL")),
        session_days=max(1, min(90, int(os.environ.get("RICEMAP_SESSION_DAYS", "14") or "14"))),
        login_max_failed_attempts=max(3, min(20, int(os.environ.get("RICEMAP_LOGIN_MAX_FAILED_ATTEMPTS", "8") or "8"))),
        login_lockout_minutes=max(5, min(120, int(os.environ.get("RICEMAP_LOGIN_LOCKOUT_MINUTES", "15") or "15"))),
        upload_storage_mode=(os.environ.get("RICEMAP_UPLOAD_STORAGE", "local") or "local").strip().lower(),
        uploads_dir=str(Path(os.environ.get("RICEMAP_UPLOADS_DIR", "") or uploads_default).expanduser().resolve()),
        upload_max_mb=max(1, min(50, int(os.environ.get("RICEMAP_UPLOAD_MAX_MB", "10") or "10"))),
        public_base_url=(os.environ.get("RICEMAP_PUBLIC_BASE_URL", "") or "").strip().rstrip("/"),
        require_https=_truthy(os.environ.get("RICEMAP_REQUIRE_HTTPS", "1" if is_prod else "0")),
        backup_configured=_truthy(os.environ.get("RICEMAP_BACKUP_CONFIGURED")),
        backup_dir=str(Path(os.environ.get("RICEMAP_BACKUP_DIR", "") or backup_default).expanduser().resolve()),
        backup_uploads_enabled=_truthy(os.environ.get("RICEMAP_BACKUP_UPLOADS", "1")),
        error_monitoring_configured=_truthy(os.environ.get("RICEMAP_ERROR_MONITORING_CONFIGURED")),
        error_log_configured=_truthy(os.environ.get("RICEMAP_ERROR_LOG_CONFIGURED", "1" if is_dev else "0")),
        request_logging_enabled=_truthy(os.environ.get("RICEMAP_REQUEST_LOGGING_ENABLED", "1" if is_dev else "0")),
        log_level=(os.environ.get("RICEMAP_LOG_LEVEL", "INFO") or "INFO").strip().upper(),
        error_log_retention_days=max(1, min(365, int(os.environ.get("RICEMAP_ERROR_LOG_RETENTION_DAYS", "30") or "30"))),
        stripe_mode=(os.environ.get("RICEMAP_STRIPE_MODE", "test" if not is_prod else "live") or "test").strip().lower(),
        deployment_provider=(os.environ.get("RICEMAP_DEPLOYMENT_PROVIDER", "local") or "local").strip().lower(),
        deployment_region=(os.environ.get("RICEMAP_DEPLOYMENT_REGION", "") or "").strip(),
        release_version=(os.environ.get("RICEMAP_RELEASE_VERSION", "step9.94-owner-access-security") or "step9.94-owner-access-security").strip(),
        git_commit_sha=(os.environ.get("RICEMAP_GIT_COMMIT_SHA", "") or "").strip(),
        port=max(1, min(65535, int(os.environ.get("PORT", "8091") or "8091"))),
    )
    if is_prod and not cfg.allow_unsafe_production:
        missing: list[str] = []
        # Admin key is deprecated for production. Admin access should use session auth.
        if not cfg.session_secret or len(cfg.session_secret) < 32:
            missing.append("RICEMAP_SESSION_SECRET must be set to a long random value")
        if not cfg.cors_allowed_origins or "*" in cfg.cors_allowed_origins:
            missing.append("CORS_ALLOWED_ORIGINS must list exact production origin(s), not '*'")
        if cfg.enable_demo_seed:
            missing.append("ENABLE_DEMO_SEED must not be enabled in production")
        if cfg.enable_legacy_admin_key or cfg.admin_key:
            missing.append("Legacy admin key fallback must be disabled in production; use admin session login")
        if not cfg.database_url:
            missing.append("DATABASE_URL must be set in production")
        if not cfg.user_data_outside_code_dir:
            missing.append("RICEMAP_DATA_DIR or external DATABASE_URL/RICEMAP_UPLOADS_DIR/RICEMAP_BACKUP_DIR must keep user data outside the replaceable code directory")
        if cfg.upload_storage_mode != "local":
            missing.append("Only local upload storage is implemented in this build; use RICEMAP_UPLOAD_STORAGE=local")
        if not cfg.uploads_dir:
            missing.append("RICEMAP_UPLOADS_DIR must be set in production")
        if not cfg.public_base_url or not cfg.public_base_url.startswith("https://"):
            missing.append("RICEMAP_PUBLIC_BASE_URL must be set to the HTTPS production URL")
        if not cfg.backup_configured:
            missing.append("RICEMAP_BACKUP_CONFIGURED=true must be set after database/upload backups are configured")
        if not cfg.backup_dir:
            missing.append("RICEMAP_BACKUP_DIR must be set in production")
        if not cfg.error_monitoring_configured:
            missing.append("RICEMAP_ERROR_MONITORING_CONFIGURED=true must be set after monitoring is configured")
        if not cfg.error_log_configured:
            missing.append("RICEMAP_ERROR_LOG_CONFIGURED=true must be set after app error logging is configured")
        if cfg.deployment_provider == "local":
            missing.append("RICEMAP_DEPLOYMENT_PROVIDER must be set in production")
        if not cfg.deployment_region:
            missing.append("RICEMAP_DEPLOYMENT_REGION should identify production region/provider location")
        if missing:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(missing))
    if cfg.upload_storage_mode not in {"local"}:
        raise RuntimeError("Unsupported RICEMAP_UPLOAD_STORAGE. This build supports local only.")
    if cfg.stripe_mode not in {"disabled", "test", "live"}:
        raise RuntimeError("Unsupported RICEMAP_STRIPE_MODE. Use disabled, test or live.")
    if cfg.deployment_provider not in {"local", "render", "railway", "fly", "digitalocean", "other"}:
        raise RuntimeError("Unsupported RICEMAP_DEPLOYMENT_PROVIDER. Use local, render, railway, fly, digitalocean or other.")
    if cfg.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise RuntimeError("Unsupported RICEMAP_LOG_LEVEL. Use DEBUG, INFO, WARNING, ERROR or CRITICAL.")
    return cfg


runtime_config = load_runtime_config()


def is_development() -> bool:
    return runtime_config.is_development


def is_staging() -> bool:
    return runtime_config.is_staging


def is_production() -> bool:
    return runtime_config.is_production
