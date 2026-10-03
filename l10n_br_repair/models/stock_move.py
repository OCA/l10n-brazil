# Copyright 2026 - TODAY, KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_repair_so_line_vals(self):
        """Sale order lines created for the repair parts get the fiscal
        operation, so CFOP and taxes are computed by l10n_br_sale."""
        vals = super()._prepare_repair_so_line_vals()
        operation = (
            self.repair_id.sale_order_id.fiscal_operation_id
            or self.repair_id.fiscal_operation_id
        )
        if operation:
            vals["fiscal_operation_id"] = operation.id
        return vals
