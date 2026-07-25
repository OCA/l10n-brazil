# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPickingVol(models.Model):
    _name = "stock.picking.vol"
    _description = "Volume Data"
    _inherit = "nfe.40.vol"

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Stock Picking",
    )
