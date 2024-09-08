# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrExpense(models.Model):
    _inherit = ["hr.expense"]

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operation",
    )

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        company_id = vals.get("company_id")

        if company_id:
            company = self.env["res.company"].browse(company_id)
        else:
            company = self.env.user.company_id

        fiscal_operation_id = company.expense_invoice_fiscal_operation_id
        if fiscal_operation_id:
            vals.update({"fiscal_operation_id": fiscal_operation_id.id})

        return vals

    def _prepare_invoice_line_values(self):
        res = super()._prepare_invoice_line_values()
        for line in res:
            line.update({"fiscal_operation_id": self.fiscal_operation_id.id})
        return res

    def _prepare_invoice_values(self):
        res = super()._prepare_invoice_values()
        res.update(
            {
                "company_id": self.company_id.id,
                "fiscal_operation_id": self.fiscal_operation_id.id,
                "fiscal_operation_type": "in",
                "document_type_id": self.fiscal_operation_id.id,
            }
        )
        return res

    def action_expense_create_invoice(self):
        super().action_expense_create_invoice()

        invoice = self.env["account.move"].search(
            [("id", "=", self.invoice_id.id)], limit=1
        )

        invoice_vals = invoice._convert_to_write(invoice._cache)
        invoice_vals.update(
            {
                "currency_id": self.currency_id.id,
            }
        )

        invoice.write(invoice_vals)

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

        return invoice
