#!/bin/bash
set -euo pipefail

# Railway sets PORT to the HTTP port the proxy expects. The official Odoo image
# uses PORT for PostgreSQL — fix that mismatch before delegating to Odoo's entrypoint.
HTTP_PORT="${PORT:-8069}"

DB_HOST_VAL=""
DB_PORT_VAL="5432"
DB_USER_VAL=""
DB_PASS_VAL=""
DB_NAME_VAL=""

if [[ -n "${PGHOST:-}" ]]; then
  DB_HOST_VAL="$PGHOST"
  DB_PORT_VAL="${PGPORT:-5432}"
  DB_USER_VAL="${PGUSER:-postgres}"
  DB_PASS_VAL="${PGPASSWORD:-}"
  DB_NAME_VAL="${PGDATABASE:-}"
elif [[ -n "${DATABASE_URL:-}" ]]; then
  eval "$(python3 <<'PY'
import os
import urllib.parse as u
import shlex

url = os.environ.get("DATABASE_URL", "").strip()
if not url:
    raise SystemExit(0)
if url.startswith("postgres://"):
    url = "postgresql://" + url[len("postgres://") :]
parsed = u.urlparse(url)
host = parsed.hostname or ""
port = str(parsed.port or 5432)
user = u.unquote(parsed.username or "")
password = u.unquote(parsed.password or "")
dbname = (parsed.path or "").lstrip("/")
print(f"DB_HOST_VAL={shlex.quote(host)}")
print(f"DB_PORT_VAL={shlex.quote(port)}")
print(f"DB_USER_VAL={shlex.quote(user)}")
print(f"DB_PASS_VAL={shlex.quote(password)}")
print(f"DB_NAME_VAL={shlex.quote(dbname)}")
PY
)"
fi

# Odoo refuses the PostgreSQL superuser name `postgres`; provision `odoo` if needed.
if [[ "${DB_USER_VAL}" == "postgres" && -n "${DATABASE_URL:-}" ]]; then
  python3 /railway_bootstrap_db.py
  DB_USER_VAL="${ODOO_DB_USER:-odoo}"
  DB_PASS_VAL="${ODOO_DB_PASSWORD:-$DB_PASS_VAL}"
fi

export HOST="$DB_HOST_VAL"
export PORT="$DB_PORT_VAL"
export USER="$DB_USER_VAL"
export PASSWORD="$DB_PASS_VAL"
export ODOO_DATABASE_NAME="$DB_NAME_VAL"

# Auto-init base only when the DB exists but has no Odoo tables (not when DB was dropped).
# Exit 2 from railway_db_ready = database missing → skip (use Database Manager / restore).
db_status=0
python3 /railway_db_ready.py || db_status=$?

# Default off: empty DB is for Restore via Database Manager. Set ODOO_AUTO_INIT_BASE=1 for greenfield (-i base).
if [[ -n "${DB_NAME_VAL}" ]] && [[ "$db_status" -eq 1 ]] && [[ "${ODOO_AUTO_INIT_BASE:-0}" == "1" ]]; then
  echo "Initializing Odoo database ${DB_NAME_VAL} (base modules only, no demo data)..." >&2
  /entrypoint.sh odoo -d "$DB_NAME_VAL" -i base --stop-after-init --without-demo=all
fi

# Sync Odoo web.base.url from WEB_BASE_URL or RAILWAY_PUBLIC_DOMAIN (fixes wrong domain / backend redirects).
if [[ -n "${DB_NAME_VAL}" ]] && [[ "$db_status" -eq 0 ]]; then
  python3 /railway_sync_web_base_url.py || true
fi

# Always reset compiled /web/assets rows so Odoo regenerates after empty filestore (see railway_repair_web_assets.py).
if [[ -n "${DB_NAME_VAL}" ]] && [[ "$db_status" -eq 0 ]]; then
  if [[ -f /railway_repair_web_assets.py ]]; then
    python3 /railway_repair_web_assets.py || echo "railway_repair_web_assets: failed (exit $?)" >&2
  else
    echo "railway-entrypoint: MISSING /railway_repair_web_assets.py — rebuild image without Docker cache" >&2
  fi
fi

# Do NOT use -d <db>: after DROP DATABASE, Odoo would crash on every request until DB exists again.
#
# db-filter: which Postgres DB names appear in Database Manager / selector.
# Default matches TechTive_* (Live / legacy Prod) while migrating DB names. Tighten later: (?i)^TechTive_Live$
# DATABASE_URL path must be your real Postgres datname (e.g. TechTive_Live). Drop ?db=TechTive_Prod bookmarks if obsolete.
# Override: ODOO_DB_FILTER e.g. .*
EXTRA=( "$@" )
if [[ ${#EXTRA[@]} -ge 1 && "${EXTRA[0]}" == "odoo" ]]; then
  EXTRA=( "${EXTRA[@]:1}" )
fi

FILTER_ARGS=()
if [[ -n "${DB_NAME_VAL}" ]]; then
  FILTER_PATTERN="${ODOO_DB_FILTER:-(?i)^TechTive_.*\$}"
  FILTER_ARGS=( "--db-filter=${FILTER_PATTERN}" )
fi

# Railway terminates TLS at the edge; Odoo must trust X-Forwarded-* so CSS/JS asset URLs use https://…
exec /entrypoint.sh odoo --http-port="$HTTP_PORT" --proxy-mode "${FILTER_ARGS[@]}" "${EXTRA[@]}"
