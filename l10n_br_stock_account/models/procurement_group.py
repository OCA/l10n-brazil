# Copyright (C) 2020  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(
        self, product_id, product_qty, product_uom, location_id, name, origin, values
    ):
        result = super().run(
            product_id, product_qty, product_uom, location_id, name, origin, values
        )

        if values.get("route_id"):
            pass

        return result
