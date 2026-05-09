#!/usr/bin/env python3
"""Exit 0 if Odoo schema exists in DB_NAME; exit 1 if empty / needs init."""
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
    except Exception:
        return 1
    try:
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.ir_module_module')")
        reg = cur.fetchone()[0]
        cur.close()
    finally:
        conn.close()
    return 0 if reg else 1


if __name__ == "__main__":
    raise SystemExit(main())
