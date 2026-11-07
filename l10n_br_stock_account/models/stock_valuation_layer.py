# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    # The core Monetary would round the net cost to the currency decimals.
    unit_cost = fields.Float(digits="Product Price")
