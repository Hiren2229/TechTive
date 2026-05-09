#!/usr/bin/env python3
"""Clear compiled /web/assets attachments so Odoo rebuilds CSS/JS from addons.

Railway’s ephemeral disk often deletes files while Postgres keeps ir_attachment rows → FileNotFoundError.

This runs every boot on DATABASE_URL’s DB (unless ODOO_SKIP_ASSET_REPAIR=1). Regeneration happens on first
HTTP hits (small overhead).

Persist /var/lib/odoo with a Railway Volume + backup restore for real attachments (PDFs, logos).
"""
from __future__ import annotations

import os
import sys

import psycopg2


def main() -> int:
    if os.environ.get("ODOO_SKIP_ASSET_REPAIR", "").strip() == "1":
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
        print(f"railway_repair_web_assets: skip (DB): {e}", file=sys.stderr)
        return 0

    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.ir_attachment')")
        if not cur.fetchone()[0]:
            return 0

        cur.execute(
            """
            DELETE FROM ir_attachment
            WHERE url LIKE '/web/assets/%%'
            """
        )
        n = cur.rowcount
        cur.close()
        if n:
            print(
                f"railway_repair_web_assets: deleted {n} /web/assets row(s) in DB {db!r} for regeneration.",
                file=sys.stderr,
            )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
