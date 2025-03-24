# Copyright (C) 2022  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class CommissionSettlement(models.Model):
    _inherit = "commission.settlement"

    def _prepare_invoice(self, journal, product, date=False):
        vals = super()._prepare_invoice(journal, product, date)
        if self.env.context.get("document_type_id"):
            vals.update(
                {
                    "document_type_id": self.env.context.get("document_type_id"),
                    "fiscal_operation_id": self.env.context.get("fiscal_operation_id"),
                    "issuer": "partner" if journal.type == "purchase" else "company",
                }
            )
            for line in vals["invoice_line_ids"]:
                line_dict = line[2]
                line_dict.update(
                    {
                        "fiscal_operation_id": self.env.context.get(
                            "fiscal_operation_id"
                        ),
                    }
                )
            invoice = self.env["account.move"].new(vals)
            for invoice_line in invoice.invoice_line_ids:
                # TODO
                # if invoice_line.invoice_id.type == "in_refund":
                #     invoice_line.price_unit = -settlement.total
                # else:
                #     invoice_line.price_unit = settlement.total
                invoice_line._onchange_fiscal_operation_id()
            vals = invoice._convert_to_write(invoice._cache)
        return vals
