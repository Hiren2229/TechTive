#!/usr/bin/env python3
"""Ensure a non-postgres DB role exists — Odoo aborts when db_user is 'postgres'."""
from __future__ import annotations

import os
import sys
import urllib.parse as u

import psycopg2
from psycopg2 import sql


def main() -> int:
    raw = os.environ.get("DATABASE_URL", "").strip()
    if not raw:
        return 0
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    parsed = u.urlparse(raw)
    admin_user = u.unquote(parsed.username or "")
    if admin_user != "postgres":
        return 0

    host = parsed.hostname or ""
    port = parsed.port or 5432
    admin_pw = u.unquote(parsed.password or "")
    dbname = (parsed.path or "").lstrip("/") or "postgres"
    odoo_user = os.environ.get("ODOO_DB_USER", "odoo")
    odoo_pw = os.environ.get("ODOO_DB_PASSWORD") or admin_pw

    admin_dsn = (
        f"host={host} port={port} dbname=postgres user={admin_user} password={admin_pw}"
    )
    conn = psycopg2.connect(admin_dsn)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (odoo_user,))
    if not cur.fetchone():
        cur.execute(
            sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD %s CREATEDB").format(
                sql.Identifier(odoo_user)
            ),
            (odoo_pw,),
        )
    cur.execute(
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(dbname), sql.Identifier(odoo_user)
        )
    )
    cur.close()
    conn.close()

    db_dsn = f"host={host} port={port} dbname={dbname} user={admin_user} password={admin_pw}"
    conn = psycopg2.connect(db_dsn)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(sql.Identifier(odoo_user))
    )
    cur.execute(
        sql.SQL("ALTER SCHEMA public OWNER TO {}").format(sql.Identifier(odoo_user))
    )
    cur.close()
    conn.close()

    print(f"Bootstrap: using PostgreSQL role {odoo_user!r} for Odoo (not postgres).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
