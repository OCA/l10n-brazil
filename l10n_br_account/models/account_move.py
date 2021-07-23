# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dateutil.relativedelta import relativedelta

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    SITUACAO_EDOC_AUTORIZADA,
)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_wh_invoice(self, move_line, fiscal_group):
        wh_date_invoice = move_line.invoice_id.date_invoice
        wh_due_invoice = wh_date_invoice.replace(day=fiscal_group.wh_due_day)
        values = {
            "partner_id": fiscal_group.partner_id.id,
            "date_invoice": wh_date_invoice,
            "date_due": wh_due_invoice + relativedelta(months=1),
            "type": "in_invoice",
            "account_id": fiscal_group.partner_id.property_account_payable_id.id,
            "journal_id": move_line.journal_id.id,
            "origin": move_line.invoice_id.number,
        }
        return values

    def _prepare_wh_invoice_line(self, invoice, move_line):
        values = {
            "name": move_line.name,
            "quantity": move_line.quantity,
            "uom_id": move_line.product_uom_id,
            "price_unit": abs(move_line.balance),
            "invoice_id": invoice.id,
            "account_id": move_line.account_id.id,
            "wh_move_line_id": move_line.id,
            "account_analytic_id": move_line.analytic_account_id.id,
        }
        return values

    def _finalize_invoices(self, invoices):
        for invoice in invoices:
            invoice.compute_taxes()
            for line in invoice.invoice_line_ids:
                # Use additional field helper function (for account extensions)
                line._set_additional_fields(invoice)
            invoice._onchange_cash_rounding()

    def create_wh_invoices(self):
        for move in self:
            for line in move.line_ids.filtered(lambda l: l.tax_line_id):
                # Create Wh Invoice only for supplier invoice
                if line.invoice_id and line.invoice_id.type != "in_invoice":
                    continue

                account_tax_group = line.tax_line_id.tax_group_id
                if account_tax_group and account_tax_group.fiscal_tax_group_id:
                    fiscal_group = account_tax_group.fiscal_tax_group_id
                    if fiscal_group.tax_withholding:
                        invoice = self.env["account.invoice"].create(
                            self._prepare_wh_invoice(line, fiscal_group)
                        )

                        self.env["account.invoice.line"].create(
                            self._prepare_wh_invoice_line(invoice, line)
                        )

                        self._finalize_invoices(invoice)
                        invoice.action_invoice_open()

    def _withholding_validate(self):
        for m in self:
            invoices = (
                self.env["account.invoice.line"]
                .search([("wh_move_line_id", "in", m.mapped("line_ids").ids)])
                .mapped("invoice_id")
            )

            invoices.filtered(lambda i: i.state == "open").action_invoice_cancel()

            invoices.filtered(lambda i: i.state == "cancel").action_invoice_draft()
            invoices.invalidate_cache()
            invoices.filtered(lambda i: i.state == "draft").unlink()

    def post(self, invoice=False):
        result = super().post(invoice)
        if invoice:
            if (
                invoice.document_type_id
                and invoice.document_electronic
                and invoice.issuer == DOCUMENT_ISSUER_COMPANY
                and invoice.state_edoc != SITUACAO_EDOC_AUTORIZADA
            ):
                self.button_cancel()
        return result

    def button_cancel(self):
        self._withholding_validate()
        return super().button_cancel()
