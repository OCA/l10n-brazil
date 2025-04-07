# Copyright (C) 2022  Renan Hiroki Bastos - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    partner_uom = fields.Char()

    partner_uom_factor = fields.Float(string="Partner UOM Factor", default=1)
