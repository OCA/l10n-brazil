# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

from .payment_provider import BRBANK


class AccountMove(models.Model):
    _inherit = "account.move"

    brbank_boleto_printable = fields.Boolean(compute="_compute_brbank_boleto_printable")
    brbank_hide_capture = fields.Boolean(
        compute="_compute_brbank_hide_capture",
        help="Every authorized transaction is a brbank title: the core Capture and "
        "Void buttons give way to Check at the bank and Write off at the bank.",
    )

    def _compute_brbank_hide_capture(self):
        for move in self:
            txs = move.authorized_transaction_ids
            move.brbank_hide_capture = bool(txs) and all(
                tx.provider_code == BRBANK for tx in txs
            )

    def _brbank_printable_transactions(self):
        """Live boletos of the invoice (Pix-only charges have no boleto)."""
        self.ensure_one()
        return self._boleto_report_transactions().filtered(
            lambda t: t.provider_code == BRBANK and (t.barcode or t.digitable_line)
        )

    def _compute_brbank_boleto_printable(self):
        for move in self:
            move.brbank_boleto_printable = bool(
                move.move_type == "out_invoice"
                and move.state == "posted"
                and move._brbank_printable_transactions()
            )

    def action_brbank_print_boletos(self):
        """One PDF with every live boleto of the invoice, attached to it."""
        self.ensure_one()
        pdfs = [
            base64.b64decode(tx.boleto_pdf)
            for tx in self._brbank_printable_transactions()
            if tx.boleto_pdf or tx._brbank_fetch_pdf(raise_reason=True)
        ]
        if not pdfs:
            raise UserError(_("No boleto of this invoice can be printed yet."))
        content = pdfs[0] if len(pdfs) == 1 else merge_pdf(pdfs)
        name = _("Boleto %s.pdf", self.name.replace("/", "-"))
        Attachment = self.env["ir.attachment"]
        attachment = Attachment.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("name", "=", name),
            ],
            limit=1,
        )
        values = {"datas": base64.b64encode(content), "mimetype": "application/pdf"}
        if attachment:
            attachment.write(values)
        else:
            attachment = Attachment.create(
                dict(values, name=name, res_model=self._name, res_id=self.id)
            )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "new",
        }

    def _compute_invoice_date_due(self):
        """Core reads the payment term: an extended boleto would go back on the
        next reconciliation."""
        res = super()._compute_invoice_date_due()
        for move in self.filtered(lambda m: m.state == "posted" and m.transaction_ids):
            dates = move.due_line_ids.filtered("date_maturity").mapped("date_maturity")
            if dates:
                move.invoice_date_due = max(dates)
        return res

    def generate_boletos(self):
        provider = self.payment_mode_id.payment_provider_id.sudo()
        if provider.code == BRBANK:
            self._brbank_create_boletos()
        return super().generate_boletos()

    def _brbank_create_boletos(self):
        """Issue one bank title per open installment without a live one."""
        self.ensure_one()
        provider = self.payment_mode_id.payment_provider_id.sudo()
        if provider.state == "disabled":
            raise UserError(
                _(
                    "The payment provider %s of the payment mode is disabled.",
                    provider.name,
                )
            )
        transactions = self.env["payment.transaction"].sudo()
        installments = self.due_line_ids.sorted(
            lambda line: (line.date_maturity, line.id)
        )
        for index, installment in enumerate(installments, start=1):
            if installment.reconciled or self._boleto_get_active_transactions(
                installment
            ):
                continue
            transaction = transactions.create(
                self._brbank_prepare_transaction_values(installment, index)
            )
            transaction._brbank_register()
            transactions |= transaction
        return transactions

    def _brbank_prepare_transaction_values(self, installment, index):
        """Values of the transaction that charges `installment`, with stable keys."""
        provider = self.payment_mode_id.payment_provider_id.sudo()
        mode = self.payment_mode_id
        attempt = len(
            self.transaction_ids.filtered(
                lambda t: t.move_line_id == installment and t.provider_code == BRBANK
            )
        )
        Transaction = self.env["payment.transaction"]
        return {
            "reference": Transaction._compute_reference(
                provider.code, prefix=f"{self.name}-{index}"
            ),
            "provider_id": provider.id,
            "partner_id": self.partner_id.commercial_partner_id.id,
            "operation": "offline",
            "is_boleto_payment": True,
            "amount": abs(installment.amount_residual_currency),
            "currency_id": self.currency_id.id,
            "due_date": installment.date_maturity,
            "boleto_penalty": mode.payment_boleto_penalty or 0.0,
            "boleto_interest": mode.payment_boleto_interest or 0.0,
            "boleto_instructions": mode.payment_boleto_instructions or "",
            "invoice_ids": [(6, 0, self.ids)],
            "move_line_id": installment.id,
            "brbank_idempotency_key": Transaction._brbank_new_idempotency_key(
                f"aml{installment.id}-{attempt}"
            ),
            "brbank_seu_numero": f"{installment.id}{attempt:02d}",
        }
