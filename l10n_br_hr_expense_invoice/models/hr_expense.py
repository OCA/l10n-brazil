# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class HrExpense(models.Model):

    _name = "hr.expense"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _fiscal_operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        company_id = vals.get("company_id")
        if company_id:
            company_id = self.env["res.company"].browse(company_id)
        else:
            company_id = self.env.user.company_id
        fiscal_operation_id = company_id.expense_invoice_fiscal_operation_id
        vals.update(
            {
                "fiscal_operation_id": fiscal_operation_id.id,
            }
        )
        return vals

    def action_expense_create_invoice(self):
        fiscal_operation_id = (self.company_id.expense_invoice_fiscal_operation_id.id,)

        invoice_lines = [
            (
                0,
                0,
                {
                    "product_id": self.product_id.id,
                    "name": self.name,
                    "price_unit": self.unit_amount,
                    "quantity": self.quantity,
                    "account_id": self.account_id.id,
                    "account_analytic_id": self.analytic_account_id.id,
                    "invoice_line_tax_ids": [(6, 0, self.tax_ids.ids)],
                    "fiscal_operation_id": fiscal_operation_id,
                },
            )
        ]
        invoice_vals = {
            "company_id": self.company_id.id,
            "type": "in_invoice",
            "fiscal_operation_id": fiscal_operation_id,
            "fiscal_operation_type": "in",
            "document_type_id": self.company_id.document_type_id.id,
            "issuer": "partner",
            "reference": self.reference,
            "date_invoice": self.date,
            "invoice_line_ids": invoice_lines,
        }

        invoice = (
            self.env["account.invoice"]
            .with_context(
                force_company=self.company_id.id,
            )
            .new(invoice_vals)
        )

        invoice_vals = invoice._convert_to_write(invoice._cache)
        invoice_vals.update(
            {
                "currency_id": self.currency_id.id,
                "origin": self.name,
            }
        )

        invoice = self.env["account.invoice"].create(invoice_vals)
        invoice.fiscal_document_id._onchange_document_serie_id()
        invoice.fiscal_document_id._onchange_company_id()

        for line in invoice.invoice_line_ids:
            line._onchange_product_id()
            line._onchange_product_id_fiscal()
            line.price_unit = self.unit_amount
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_tax_ids()

        invoice._onchange_invoice_line_ids()

        self.write(
            {
                "invoice_id": invoice.id,
                "quantity": 1,
                "tax_ids": [(5,)],
                "unit_amount": invoice.amount_total,
            }
        )
        return True
