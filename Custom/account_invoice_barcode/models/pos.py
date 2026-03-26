# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from random import randint

class AccountMove(models.Model):
    _inherit = 'account.move'

    barcode = fields.Char("Barcode")

    _sql_constraints = [
        ('barcod_uniq', 'unique(barcode)', 'Unique Barcode not allowed.')
    ]

    # @api.multi
    def generate_barcode(self):
        for res in self:
            i = True
            while i:
                barcode = ''.join(["%s" % randint(0, 9) for num in range(0, 13)])
                sale_order = self.search([('barcode','=',barcode)])
                if len(sale_order) <= 0:
                    res.barcode = barcode
                    i = False