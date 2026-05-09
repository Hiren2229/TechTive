#!/bin/bash
set -euo pipefail

# Railway sets PORT to the HTTP port the proxy expects. The official Odoo image
# uses PORT for PostgreSQL — fix that mismatch before delegating to Odoo's entrypoint.
HTTP_PORT="${PORT:-8069}"

DB_HOST_VAL=""
DB_PORT_VAL="5432"
DB_USER_VAL=""
DB_PASS_VAL=""

if [[ -n "${PGHOST:-}" ]]; then
  DB_HOST_VAL="$PGHOST"
  DB_PORT_VAL="${PGPORT:-5432}"
  DB_USER_VAL="${PGUSER:-postgres}"
  DB_PASS_VAL="${PGPASSWORD:-}"
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
print(f"DB_HOST_VAL={shlex.quote(host)}")
print(f"DB_PORT_VAL={shlex.quote(port)}")
print(f"DB_USER_VAL={shlex.quote(user)}")
print(f"DB_PASS_VAL={shlex.quote(password)}")
PY
)"
fi

export HOST="$DB_HOST_VAL"
export PORT="$DB_PORT_VAL"
export USER="$DB_USER_VAL"
export PASSWORD="$DB_PASS_VAL"

# Docker CMD is typically `odoo`; avoid passing it twice to the stock entrypoint.
EXTRA=( "$@" )
if [[ ${#EXTRA[@]} -ge 1 && "${EXTRA[0]}" == "odoo" ]]; then
  EXTRA=( "${EXTRA[@]:1}" )
fi
exec /entrypoint.sh odoo --http-port="$HTTP_PORT" "${EXTRA[@]}"
