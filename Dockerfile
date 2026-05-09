FROM odoo:16

USER root

COPY account_invoice_barcode /mnt/extra-addons/account_invoice_barcode
COPY invoice_format_editor /mnt/extra-addons/invoice_format_editor
COPY project_scrum /mnt/extra-addons/project_scrum
COPY project_timeline /mnt/extra-addons/project_timeline
COPY web_timeline /mnt/extra-addons/web_timeline

COPY railway-entrypoint.sh /railway-entrypoint.sh
RUN chmod +x /railway-entrypoint.sh \
    && chown -R odoo:odoo /mnt/extra-addons

USER odoo

ENTRYPOINT ["/railway-entrypoint.sh"]
CMD ["odoo"]
