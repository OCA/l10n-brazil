# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dataclasses import replace
from datetime import date

from odoo import _, api, fields, models
from odoo.tools import frozendict

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_COMPANY
from odoo.addons.l10n_br_fiscal_edi.tools import EdiInstallment, EdiPayment

PAYABLE_RECEIVABLE = ("asset_receivable", "liability_payable")


class AccountMove(models.Model):
    _inherit = "account.move"

    edi_payment_summary = fields.Html(
        compute="_compute_edi_payment_summary",
        sanitize=False,
        help="Installments and payment that the fiscal document will declare, "
        "to check before posting the invoice. It is not stored.",
    )

    ###################
    # Imported document
    ###################

    def _compute_imported_terms(self):
        """The due dates of the installments the imported document declares.

        The invoice total is the net amount payable, which may differ from what
        the installments add up to: each installment takes its share of the total
        by its weight, and the last one the rounding residue.
        """
        self.ensure_one()
        document = self.fiscal_document_id
        installments = document._edi_get_installments()
        declared = sum(installment.amount for installment in installments)
        if not declared or len(self.invoice_line_ids) < len(document.fiscal_line_ids):
            return False
        sign = 1 if self.is_inbound(include_receipts=True) else -1
        amounts = [
            self.currency_id.round(self.amount_total * installment.amount / declared)
            for installment in installments
        ]
        amounts[-1] = self.currency_id.round(self.amount_total - sum(amounts[:-1]))
        for installment, amount in zip(installments, amounts, strict=True):
            key = frozendict(
                {
                    "move_id": self.id,
                    "date_maturity": installment.date_due,
                    "discount_date": False,
                    "discount_percentage": 0,
                }
            )
            balance = self.currency_id._convert(
                amount,
                self.company_currency_id,
                self.company_id,
                self.invoice_date or fields.Date.context_today(self),
            )
            term = self.needed_terms.setdefault(
                key, {"balance": 0.0, "amount_currency": 0.0}
            )
            term["balance"] += sign * balance
            term["amount_currency"] += sign * amount
        return True

    ################################
    # Installments and payments
    ################################

    def _edi_installments(self):
        """The installments of the invoice, by due date.

        On a draft the lines of the installments are only brought up to date
        when the invoice is saved, so the preview reads the terms that the
        invoice will give them (`needed_terms`), which is what the lines hold
        once they are written."""
        self.ensure_one()
        if self.state == "draft" and self.needed_terms:
            terms = sorted(
                self.needed_terms.items(),
                key=lambda item: item[0]["date_maturity"] or date.max,
            )
            return [
                EdiInstallment(
                    number=str(number).zfill(3),
                    date_due=key["date_maturity"],
                    amount=abs(values["amount_currency"]),
                )
                for number, (key, values) in enumerate(terms, 1)
            ]
        due_lines = self.line_ids.filtered(
            lambda line: (
                line.account_id.account_type in PAYABLE_RECEIVABLE
                and line.date_maturity
            )
        ).sorted("date_maturity")
        return [
            EdiInstallment(
                number=str(number).zfill(3),
                date_due=line.date_maturity,
                amount=abs(line.amount_currency),
            )
            for number, line in enumerate(due_lines, 1)
        ]

    def _edi_payments(self):
        """The payment of the invoice: in cash, or in installments when a due date
        goes beyond the date of the invoice."""
        self.ensure_one()
        reference = self.invoice_date or self.date
        on_terms = any(
            installment.date_due > reference for installment in self._edi_installments()
        )
        return [
            EdiPayment(
                means=self._edi_payment_means(),
                amount=self.amount_financial_total,
                term="installments" if on_terms else "cash",
            )
        ]

    def _edi_payment_means(self):
        """Code of the means of payment of the document. Who knows the payment
        mode of the invoice overrides it."""
        self.ensure_one()
        return ""

    @api.depends(
        "line_ids.date_maturity",
        "line_ids.amount_currency",
        "invoice_payment_term_id",
        "invoice_date",
        "amount_financial_total",
    )
    def _compute_edi_payment_summary(self):
        for move in self:
            if (
                move.state != "draft"
                or not move.document_type_id
                or move.issuer != DOCUMENT_ISSUER_COMPANY
                or move.imported_document
            ):
                move.edi_payment_summary = False
                continue
            move.edi_payment_summary = self.env["ir.qweb"]._render(
                "l10n_br_fiscal_edi.document_payment_summary",
                {
                    "currency": move.currency_id,
                    "installments": move._edi_installments(),
                    "payments": [
                        replace(
                            payment,
                            label=move.fiscal_document_id._edi_payment_means_label(
                                payment.means
                            ),
                        )
                        for payment in move._edi_payments()
                    ],
                    "totals": [
                        (
                            _("Document total"),
                            move.fiscal_amount_total + move.amount_tax_withholding,
                        ),
                        (_("Withholdings"), move.amount_tax_withholding),
                        (_("Net amount payable"), move.fiscal_amount_total),
                    ],
                    "warning": False,
                },
            )

    def _post(self, soft=True):
        """The tags of the issued document are written here, from what the invoice
        pays, before the document is confirmed. Until then the page of the
        installments is only a preview."""
        for move in self.filtered(lambda m: m.state == "draft"):
            if not move.invoice_date and move.is_sale_document(include_receipts=True):
                # the date that the posting would give: the due dates follow it
                move.invoice_date = fields.Date.context_today(move)
            for document in move.fiscal_document_ids.filtered(
                lambda d: (
                    d.document_type_id
                    and d.issuer == DOCUMENT_ISSUER_COMPANY
                    and not d.imported_document
                )
            ):
                document._edi_set_installments(move._edi_installments())
                document._edi_set_payments(move._edi_payments())
        return super()._post(soft=soft)
