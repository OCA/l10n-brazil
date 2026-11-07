# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        """l10n_br_sale_stock puts the sale order fiscal operation on pickings
        of sale moves; rental transfers keep the operation of their moves."""
        values = super()._get_new_picking_values()
        move = self[:1]
        if move.picking_type_id.l10n_br_rental_kind:
            values["fiscal_operation_id"] = move.fiscal_operation_id.id
            values["invoice_state"] = move.invoice_state
        return values
