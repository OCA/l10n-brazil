# Copyright 2026 - TODAY, KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _get_repair_ids_from_commands(self, commands):
        repair_ids = []
        for command in commands or []:
            if command[0] == 4:
                repair_ids.append(command[1])
            elif command[0] == 6:
                repair_ids.extend(command[2])
        return repair_ids

    @api.model_create_multi
    def create(self, vals_list):
        """The quotation created from a repair order takes the fiscal
        operation of the repair instead of the default sale one."""
        for vals in vals_list:
            if "fiscal_operation_id" in vals:
                continue
            repair_ids = self._get_repair_ids_from_commands(
                vals.get("repair_order_ids")
            )
            repairs = self.env["repair.order"].browse(repair_ids)
            operation = repairs.fiscal_operation_id[:1]
            if operation:
                vals["fiscal_operation_id"] = operation.id
        return super().create(vals_list)
