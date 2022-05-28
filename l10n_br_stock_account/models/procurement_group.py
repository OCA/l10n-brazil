# Copyright (C) 2020  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(self, procurements, raise_user_error=True):
        result = super().run(procurements, raise_user_error=raise_user_error)

        for procurement in procurements:
            if procurement.values.get("route_ids"):
                pass

        return result
