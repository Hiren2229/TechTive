#!/usr/bin/env python3
"""Keep ir.config_parameter web.base.url aligned with the public URL (Railway / custom domain)."""
from __future__ import annotations

import os
import sys

import psycopg2


def _resolve_public_url() -> str | None:
    raw = os.environ.get("WEB_BASE_URL", "").strip()
    if raw:
        return raw.rstrip("/")
    domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if domain:
        domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
        return f"https://{domain}".rstrip("/")
    return None


def main() -> int:
    base = _resolve_public_url()
    if not base:
        return 0

    db = os.environ.get("ODOO_DATABASE_NAME", "").strip()
    if not db:
        return 0

    try:
        conn = psycopg2.connect(
            host=os.environ.get("HOST", ""),
            port=os.environ.get("PORT", "5432"),
            user=os.environ.get("USER", ""),
            password=os.environ.get("PASSWORD", ""),
            dbname=db,
            connect_timeout=15,
        )
    except Exception as e:
        print(f"railway_sync_web_base_url: skip (no DB connection): {e}", file=sys.stderr)
        return 0

    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.ir_config_parameter')")
        if not cur.fetchone()[0]:
            return 0

        # Allow updating base URL when behind Railway / changing domains
        cur.execute(
            "UPDATE ir_config_parameter SET value = 'False' WHERE key = 'web.base.url.freeze'"
        )

        cur.execute(
            """UPDATE ir_config_parameter SET value = %s,
                   write_date = NOW() AT TIME ZONE 'UTC', write_uid = 1
               WHERE key = 'web.base.url'""",
            (base + "/",),
        )
        if cur.rowcount == 0:
            print(
                "railway_sync_web_base_url: web.base.url not in DB yet; "
                "open Odoo once on the Railway URL or set WEB_BASE_URL after DB exists.",
                file=sys.stderr,
            )
        cur.close()
        print(f"railway_sync_web_base_url: web.base.url -> {base}/", file=sys.stderr)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
