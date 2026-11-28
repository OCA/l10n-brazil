# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from urllib.parse import quote_plus

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

    def _boleto_digitable_line_display(self):
        """The digitable line grouped as printed on the boleto, for reading.

        47 digits (bank boleto): AAAAA.AAAAA BBBBB.BBBBBB CCCCC.CCCCCC D EEEE...;
        48 digits (collection slip): four blocks of 12. Anything else is kept as is.
        """
        self.ensure_one()
        digits = "".join(c for c in self.digitable_line or "" if c.isdigit())
        if len(digits) == 47:
            return (
                f"{digits[0:5]}.{digits[5:10]} {digits[10:15]}.{digits[15:21]} "
                f"{digits[21:26]}.{digits[26:32]} {digits[32]} {digits[33:]}"
            )
        if len(digits) == 48:
            return " ".join(digits[i : i + 12] for i in range(0, 48, 12))
        return self.digitable_line or ""

    def _boleto_is_overdue(self):
        """Open and past the due date, counted in the payer's day.

        The portal runs as the public or a technical user, whose timezone says
        nothing about the payer: an installment due today would read as overdue
        in the Brazilian evening.
        """
        self.ensure_one()
        if self.state == "done" or not self.due_date:
            return False
        tz = self.partner_id.tz or self.company_id.partner_id.tz or "America/Sao_Paulo"
        return self.due_date < fields.Date.context_today(self.with_context(tz=tz))

    def _boleto_pix_qr_url(self, size=400):
        """URL of the Pix QR code image, drawn by the public barcode route."""
        self.ensure_one()
        if not self.pix_copia_cola:
            return ""
        return (
            f"/report/barcode/?barcode_type=QR&value={quote_plus(self.pix_copia_cola)}"
            f"&width={size}&height={size}"
        )

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
