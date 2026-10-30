# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        """l10n_br_stock_account carries the rule fiscal operation only on pull
        rules; the rental return comes from a push rule."""
        values = super()._push_prepare_move_copy_values(move_to_copy, new_date)
        if self.picking_type_id.l10n_br_rental_kind != "retorno":
            return values
        values["fiscal_operation_id"] = self.fiscal_operation_id.id
        values["invoice_state"] = self.invoice_state
        lessee = (
            move_to_copy.sale_line_id.order_id.partner_id or move_to_copy.partner_id
        ).commercial_partner_id
        if lessee.ind_ie_dest == "1":
            # an ICMS taxpayer lessee issues the return NF-e itself (CFOP
            # 5909/6909); the company only records it
            values["invoice_state"] = "none"
        return values

    def _run_push(self, move):
        new_move = super()._run_push(move)
        if new_move and self.picking_type_id.l10n_br_rental_kind == "retorno":
            # the push copies the remessa move with its fiscal data (operation
            # line, CFOP 5908, CSTs): map them again for the return operation
            new_move._compute_fiscal_operation_line_id()
            new_move._compute_fiscal_tax_ids()
        return new_move
