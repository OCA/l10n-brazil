# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Renato Lima <renato.lima@akretion.com.br>
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, models


class CommissionSettlement(models.Model):
    _inherit = "commission.settlement"

    def _prepare_invoice(self, journal, product, date=False):
        vals = super()._prepare_invoice(journal, product, date)
        if self.env.context.get("document_type_id"):
            document_type = self.env["l10n_br_fiscal.document.type"].browse(
                self.env.context.get("document_type_id")
            )

            doc_serie = False
            if document_type:
                fiscal_op = self.env["l10n_br_fiscal.operation"].browse(
                    self.env.context.get("fiscal_operation_id")
                )
                document_serie = document_type.get_document_serie(
                    self.env.company, fiscal_op
                )
                if document_serie:
                    doc_serie = document_serie

            vals.update(
                {
                    "document_type_id": self.env.context.get("document_type_id"),
                    "document_serie_id": doc_serie.id,
                    "fiscal_operation_id": self.env.context.get("fiscal_operation_id"),
                    "issuer": "partner" if journal.type == "purchase" else "company",
                }
            )

            invoice = self.env["account.move"].new(vals)
            invoice._onchange_partner_id()
            invoice._inverse_company_id()
            invoice._inverse_currency_id()
            invoice._onchange_date()
            vals = invoice._convert_to_write(invoice._cache)

            new_invoice_line_ids = []
            for line in vals.get("invoice_line_ids"):
                if line[2]:
                    line_dict = line[2]
                    line_dict.update(
                        {
                            "move_id": invoice.id,
                            "fiscal_operation_id": self.env.context.get(
                                "fiscal_operation_id"
                            ),
                        }
                    )
                    line_obj = self.env["account.move.line"]
                    values = line_obj.default_get(line_obj.fields_get().keys())
                    values.update(line_dict)
                    move_line = self.env["account.move.line"].new(values.copy())
                    move_line._inverse_partner_id()
                    move_line._inverse_product_id()
                    move_line._inverse_account_id()
                    move_line._inverse_amount_currency()
                    # Fiscal Brazil:
                    move_line._onchange_fiscal_operation_id()

                    new_values = move_line._convert_to_write(move_line._cache)
                    new_values.update(values)
                    new_invoice_line_ids.append(Command.create(new_values))

            vals["invoice_line_ids"] = new_invoice_line_ids

        return vals
