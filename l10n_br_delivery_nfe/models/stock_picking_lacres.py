# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockPickingLacres(models.Model):
    _name = "stock.picking.lacres"
    _description = "lacres"
    _inherit = "nfe.40.lacres"
