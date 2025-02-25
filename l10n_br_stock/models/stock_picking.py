# Copyright (C) 2016  Hendrix Costa - KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    legal_name = fields.Char(string="Legal Name", related="partner_id.legal_name")
    inscr_est = fields.Char(string="State Tax Number", related="partner_id.inscr_est")
