# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
    FISCAL_IN_OUT_ALL,
    FISCAL_OUT,
    MODELO_FISCAL_NFE,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_EM_DIGITACAO,
)

MOVE_TO_OPERATION = {
    "out_invoice": "out",
    "in_invoice": "in",
    "out_refund": "in",
    "in_refund": "out",
    "out_receipt": "out",
    "in_receipt": "in",
}

REFUND_TO_OPERATION = {
    "out_invoice": "in",
    "in_invoice": "out",
    "out_refund": "out",
    "in_refund": "in",
}

FISCAL_TYPE_REFUND = {
    "out": ["purchase_refund", "in_return"],
    "in": ["sale_refund", "out_return"],
}

MOVE_TAX_USER_TYPE = {
    "out_invoice": "sale",
    "in_invoice": "purchase",
    "out_refund": "sale",
    "in_refund": "purchase",
}

SHADOWED_FIELDS = [
    "partner_id",
    "company_id",
    "currency_id",
    "partner_shipping_id",
    "user_id",
]


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_wh_invoice(self, move_line, fiscal_group):
        wh_date_invoice = move_line.move_id.date
        wh_due_invoice = wh_date_invoice.replace(day=fiscal_group.wh_due_day)
        values = {
            "partner_id": fiscal_group.partner_id.id,
            "date": wh_date_invoice,
            "date_due": wh_due_invoice + relativedelta(months=1),
            "type": "in_invoice",
            "account_id": fiscal_group.partner_id.property_account_payable_id.id,
            "journal_id": move_line.journal_id.id,
            "origin": move_line.move_id.name,
        }
        return values

    def _prepare_wh_invoice_line(self, invoice, move_line):
        values = {
            "name": move_line.name,
            "quantity": move_line.quantity,
            "uom_id": move_line.product_uom_id,
            "price_unit": abs(move_line.balance),
            "move_id": invoice.id,
            "account_id": move_line.account_id.id,
            "wh_move_line_id": move_line.id,
            "account_analytic_id": move_line.analytic_account_id.id,
        }
        return values

    def _finalize_invoices(self, invoices):
        for invoice in invoices:
            invoice.compute_taxes()
            for line in invoice.line_ids:
                # Use additional field helper function (for account extensions)
                line._set_additional_fields(invoice)
            invoice._onchange_cash_rounding()

    def create_wh_invoices(self):
        for move in self:
            for line in move.line_ids.filtered(lambda l: l.tax_line_id):
                # Create Wh Invoice only for supplier invoice
                if line.move_id and line.move_id.type != "in_invoice":
                    continue

                account_tax_group = line.tax_line_id.tax_group_id
                if account_tax_group and account_tax_group.fiscal_tax_group_id:
                    fiscal_group = account_tax_group.fiscal_tax_group_id
                    if fiscal_group.tax_withholding:
                        invoice = self.env["account.move"].create(
                            self._prepare_wh_invoice(line, fiscal_group)
                        )

                        self.env["account.move.line"].create(
                            self._prepare_wh_invoice_line(invoice, line)
                        )

                        self._finalize_invoices(invoice)
                        invoice.action_post()

    def _withholding_validate(self):
        for m in self:
            invoices = (
                self.env["account.move.line"]
                .search([("wh_move_line_id", "in", m.mapped("line_ids").ids)])
                .mapped("move_id")
            )
            invoices.filtered(lambda i: i.state == "open").button_cancel()
            invoices.filtered(lambda i: i.state == "cancel").button_draft()
            invoices.invalidate_cache()
            invoices.filtered(lambda i: i.state == "draft").unlink()

    def post(self, invoice=False):
        # TODO FIXME migrate: no more invoice keyword
        result = super().post()
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
        for doc in self.filtered(lambda d: d.document_type_id):
            doc.fiscal_document_id.action_document_cancel()
        # Esse método é responsavel por verificar se há alguma fatura de impostos
        # retidos associada a essa fatura e cancela-las também.
        self._withholding_validate()
        return super().button_cancel()

    # TODO: Por ora esta solução contorna o problema
    #  AttributeError: 'Boolean' object has no attribute 'depends_context'
    #  Este erro está relacionado com o campo active implementado via localização
    #  nos modelos account.move.line e l10n_br_fiscal.document.line
    #  Este problema começou após este commit:
    #  https://github.com/oca/ocb/commit/1dcd071b27779e7d6d8f536c7dce7002d27212ba
    def _get_integrity_hash_fields_and_subfields(self):
        return self._get_integrity_hash_fields() + [
            f"line_ids.{subfield}"
            for subfield in self.env["account.move.line"]._get_integrity_hash_fields()
        ]
