FROM odoo:16

# Do not use Dockerfile VOLUME — Railway rejects it. Add a Railway Volume mounted at /var/lib/odoo on the TechTive service instead.

USER root

COPY account_invoice_barcode /mnt/extra-addons/account_invoice_barcode
COPY invoice_format_editor /mnt/extra-addons/invoice_format_editor
COPY project_scrum /mnt/extra-addons/project_scrum
COPY project_timeline /mnt/extra-addons/project_timeline
COPY web_timeline /mnt/extra-addons/web_timeline

COPY railway_bootstrap_db.py /railway_bootstrap_db.py
COPY railway_db_ready.py /railway_db_ready.py
COPY railway_sync_web_base_url.py /railway_sync_web_base_url.py
COPY railway_repair_web_assets.py /railway_repair_web_assets.py
COPY railway-entrypoint.sh /railway-entrypoint.sh
# Persist default DB in the image (SSH/container edits to /etc/odoo/odoo.conf do not survive redeploys).
# Railway DATABASE_URL must end with the same Postgres datname, e.g. ...postgresql://...@host:port/TT_Prod
RUN if grep -q '^db_name[[:space:]]*=' /etc/odoo/odoo.conf 2>/dev/null; then \
      sed -i 's/^db_name[[:space:]]=.*/db_name = TT_Prod/' /etc/odoo/odoo.conf; \
    else \
      sed -i '/^\[options\]/a db_name = TT_Prod' /etc/odoo/odoo.conf; \
    fi \
    && grep -q '^db_name = TT_Prod' /etc/odoo/odoo.conf
RUN chmod +x /railway-entrypoint.sh /railway_bootstrap_db.py /railway_db_ready.py /railway_sync_web_base_url.py /railway_repair_web_assets.py \
    && test -f /railway_repair_web_assets.py \
    && chown -R odoo:odoo /mnt/extra-addons

USER odoo

ENTRYPOINT ["/railway-entrypoint.sh"]
CMD ["odoo"]
