from odoo import _, models
from odoo.exceptions import UserError

# Estados em que o boleto da parcela ainda vale no banco.
BOLETO_ACTIVE_STATES = ("draft", "pending", "authorized", "done")


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()
        for move in self:
            if move.payment_mode_id.generate_boletos_on_invoice:
                move.generate_boletos()

        return res

    def generate_boletos(self):
        self.ensure_one()
        if not self.payment_mode_id.payment_provider_id:
            raise UserError(
                _(
                    "Could not generate the boletos. No payment provider is "
                    "configured for the selected payment method"
                )
            )

    def _boleto_get_active_transactions(self, moveline):
        """Live boleto transactions of an installment."""
        self.ensure_one()
        return self.transaction_ids.filtered(
            lambda t: t.move_line_id == moveline and t.state in BOLETO_ACTIVE_STATES
        )

    def _boleto_report_transactions(self):
        """Open boletos and Pix charges of the invoice, for the PDF and the portal."""
        self.ensure_one()
        return (
            self.sudo()
            .transaction_ids.filtered(
                lambda t: t.is_boleto_payment
                and t.state in ("pending", "authorized")
                and (t.digitable_line or t.pix_copia_cola)
            )
            .sorted(lambda t: (t.due_date or t.create_date.date(), t.id))
        )
