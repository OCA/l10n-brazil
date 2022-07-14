# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _add_delivery_cost_to_so(self):
        # disable this function since, if called, adds a delivery line to
        # order -> strategy no longer used, view amount_freight
        return
