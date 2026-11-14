# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    is_boleto_payment = fields.Boolean("Is boleto payment")
    due_date = fields.Date()
    our_number = fields.Char()
    digitable_line = fields.Char()
    barcode = fields.Char()
    boleto_pdf = fields.Binary(string="Boleto PDF")
    pix_copia_cola = fields.Text(string="Pix Copy and Paste", readonly=True, copy=False)
    txid = fields.Char(string="Pix TXID", readonly=True, copy=False, index=True)
    boleto_penalty = fields.Float(
        string="Penalty",
        help=(
            "Penalty fee for overdue payments. "
            "This value will be added to the total amount of the invoice."
        ),
    )
    boleto_interest = fields.Float(
        string="Interest",
        help=(
            "Interest fee for overdue payments. "
            "This value will be added to the total amount of the invoice."
        ),
    )
    boleto_instructions = fields.Text(
        string="Instructions",
        help=(
            "Instructions to be printed on the boleto. "
            "This field is used to provide additional information to the payer."
        ),
    )
    provider_technical_info = fields.Text(
        string="Technical Information",
        help="Technical information about the payment transaction.",
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Installment",
        readonly=True,
        index=True,
        ondelete="restrict",
        help="Receivable line (installment) charged by this boleto. When set, "
        "the payment reconciles only this installment.",
    )

    def _create_payment(self, **extra_create_values):
        """Settle only the installment of the boleto, not the oldest open one."""
        payment = super()._create_payment(**extra_create_values)
        if self.move_line_id:
            self._boleto_reconcile_installment(payment)
        return payment

    def _boleto_reconcile_installment(self, payment):
        """Reconcile the payment with the boleto installment; any excess stays open."""
        self.ensure_one()
        counterpart = payment.move_id.line_ids.filtered(
            lambda line: line.account_id == payment.destination_account_id
        )
        counterpart.remove_move_reconcile()
        installment = self.move_line_id
        if installment.reconciled or installment.account_id != counterpart.account_id:
            return
        (counterpart + installment).reconcile()

    def generate_boleto(self):
        raise NotImplementedError

    def _update_transaction_with_boleto_info(self, boleto_response):
        raise NotImplementedError

    def _prepare_transaction_boleto_info(self, boleto_response):
        return {
            "our_number": "",
            "digitable_line": "",
            "barcode": "",
            "boleto_pdf": "",
        }
