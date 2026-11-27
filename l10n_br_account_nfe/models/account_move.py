# Copyright 2025-TODAY Akretion - Raphaẽl Valyi <raphael.valyi@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dataclasses import replace

from odoo import api, models

from odoo.addons.l10n_br_nfe.constants.nfe import SEM_PAGAMENTO


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("payment_mode_id")
    def _compute_edi_payment_summary(self):
        """The means of payment comes from the payment mode, so the preview of
        the payment has to follow it as it is chosen or cleared."""
        return super()._compute_edi_payment_summary()

    def _edi_payment_means(self):
        """The means of payment of the NF-e is the one of the payment mode, and
        an invoice without a payment mode is not paid."""
        self.ensure_one()
        if not self.payment_mode_id:
            return SEM_PAGAMENTO
        return self.payment_mode_id.fiscal_payment_mode or ""

    def _edi_payments(self):
        """An invoice without a payment mode is not paid: the NF-e declares no
        payment for it, and so does what the invoice shows before it is posted."""
        payments = super()._edi_payments()
        if self._edi_payment_means() != SEM_PAGAMENTO:
            return payments
        return [replace(payment, amount=0.0, term="cash") for payment in payments]

    def _reverse_moves(self, default_values_list=None, cancel=False):
        new_moves = super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )
        if self.env.context.get("payment_mode_id"):
            payment_mode = self.env["account.payment.mode"].browse(
                self.env.context.get("payment_mode_id")
            )
            for move in new_moves:
                if move.company_id.country_id.code == "BR":
                    move.payment_mode_id = payment_mode

        return new_moves
