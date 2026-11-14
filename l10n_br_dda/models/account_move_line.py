# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError

from ..constants import ACTIVE_STATES, ALLOCATION_MODEL, DEBIT_MODEL


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        """Copy the digitable line, bar code and difference of the DDA boleto."""
        vals = super()._prepare_payment_line_vals(payment_order)
        allocation = (
            self.env[ALLOCATION_MODEL]
            .sudo()
            .search(
                [
                    ("move_line_id", "=", self.id),
                    ("debit_id.state", "in", ACTIVE_STATES),
                ],
                limit=1,
            )
        )
        if allocation:
            debit = allocation.debit_id
            first = debit.allocation_ids.sorted("id")[:1].move_line_id
            if self != first:
                raise UserError(
                    _(
                        "%(line)s is paid by the DDA boleto %(boleto)s, which goes "
                        "to the payment order on %(first)s.",
                        line=self.display_name,
                        boleto=debit.display_name,
                        first=first.display_name,
                    )
                )
            vals.update(debit._dda_payment_line_vals(self))
        return vals

    def reconcile(self):
        res = super().reconcile()
        self.env[DEBIT_MODEL].sudo()._dda_settle_installments(self)
        return res


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    @api.model_create_multi
    def create(self, vals_list):
        partials = super().create(vals_list)
        lines = partials.debit_move_id | partials.credit_move_id
        self.env[DEBIT_MODEL].sudo()._dda_on_reconcile(lines)
        return partials
