FROM odoo:16

USER root

COPY account_invoice_barcode /mnt/extra-addons/account_invoice_barcode
COPY invoice_format_editor /mnt/extra-addons/invoice_format_editor
COPY project_scrum /mnt/extra-addons/project_scrum
COPY project_timeline /mnt/extra-addons/project_timeline
COPY web_timeline /mnt/extra-addons/web_timeline

COPY railway_bootstrap_db.py /railway_bootstrap_db.py
COPY railway_db_ready.py /railway_db_ready.py
COPY railway-entrypoint.sh /railway-entrypoint.sh
RUN chmod +x /railway-entrypoint.sh /railway_bootstrap_db.py /railway_db_ready.py \
    && chown -R odoo:odoo /mnt/extra-addons

USER odoo

ENTRYPOINT ["/railway-entrypoint.sh"]
CMD ["odoo"]
