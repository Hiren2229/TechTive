#!/usr/bin/env python3
"""Auto-fix missing bundled CSS/JS after filestore loss (ephemeral disk on Railway).

Odoo keeps rows in ir_attachment for compiled bundles under URLs /web/assets/… while files live under
data_dir/filestore/<dbname>. If the container filesystem was wiped, requests 500 with FileNotFoundError.

On each boot we sample on-disk paths; if any sample is missing, we DELETE those attachment rows so Odoo
regenerates bundles from addons.

Opt out: ODOO_SKIP_ASSET_REPAIR=1

User uploads (PDFs, etc.) are NOT touched—only url LIKE '/web/assets/%'. For persistence mount a
Railway Volume on /var/lib/odoo and restore filestore from backup.
"""
from __future__ import annotations

import os
import sys

import psycopg2

DATA_DIR = os.environ.get("ODOO_DATA_DIR", "/var/lib/odoo").rstrip("/")
SAMPLE_LIMIT = 15


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
            SELECT store_fname FROM ir_attachment
            WHERE url LIKE '/web/assets/%%' AND store_fname IS NOT NULL
            LIMIT %s
            """,
            (SAMPLE_LIMIT,),
        )
        paths = [r[0] for r in cur.fetchall() if r and r[0]]
        if not paths:
            cur.close()
            return 0

        fs_root = os.path.join(DATA_DIR, "filestore", db)
        broken = False
        for rel in paths:
            full = os.path.join(fs_root, rel)
            if not os.path.isfile(full):
                broken = True
                break

        if not broken:
            cur.close()
            return 0

        cur.execute(
            """
            DELETE FROM ir_attachment
            WHERE url LIKE '/web/assets/%%'
            """
        )
        n = cur.rowcount
        cur.close()
        print(
            f"railway_repair_web_assets: filestore incomplete under {fs_root!r}; "
            f"removed {n} /web/assets attachment row(s) for regeneration.",
            file=sys.stderr,
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
