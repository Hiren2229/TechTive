#!/usr/bin/env python3
"""Remove broken bundled asset attachments so Odoo regenerates CSS/JS from module static files.

Odoo stores compiled bundles under ir_attachment URLs like /web/assets/… on disk in filestore.
Railway containers lose /var/lib/odoo on redeploy while Postgres survives → FileNotFoundError on /web.

Set ODOO_REPAIR_WEB_ASSETS=1 once on TechTive, redeploy, verify UI, then remove the variable.

Does not restore user uploads (PDFs, logos); add a Railway Volume on /var/lib/odoo + restore backup for that.
"""
from __future__ import annotations

import os
import sys

import psycopg2


def main() -> int:
    if os.environ.get("ODOO_REPAIR_WEB_ASSETS", "").strip() != "1":
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
        print(f"railway_repair_web_assets: skip: {e}", file=sys.stderr)
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
            WHERE url LIKE '/web/assets/%'
            """
        )
        n = cur.rowcount
        cur.close()
        print(f"railway_repair_web_assets: deleted {n} stale /web/assets attachment row(s).", file=sys.stderr)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
