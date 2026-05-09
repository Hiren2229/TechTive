#!/usr/bin/env python3
"""Check Odoo DB state for the entrypoint.

Exit codes:
  0 — database exists and ``base`` is installed (Odoo can serve HTTP).
  1 — database exists but is not initialized (run ``-i base`` unless skipped).
  2 — database does not exist (skip auto-init; create DB or restore elsewhere).
"""
from __future__ import annotations

import os
import sys

import psycopg2


def main() -> int:
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
    except psycopg2.OperationalError as e:
        msg = str(e).lower()
        if "does not exist" in msg:
            return 2
        return 1
    except Exception:
        return 1
    try:
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.ir_module_module')")
        if not cur.fetchone()[0]:
            cur.close()
            return 1
        cur.execute(
            "SELECT state FROM ir_module_module WHERE name = %s",
            ("base",),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()
    if not row or row[0] != "installed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
