# Copyright (C) 2022  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class Settlement(models.Model):
    _inherit = "sale.commission.settlement"

    def _prepare_invoice_header(self, settlement, journal, date=False):
        invoice_dict = super()._prepare_invoice_header(settlement, journal, date)
        if self.env.context.get("document_type_id"):
            invoice_dict.update(
                {
                    "document_type_id": self.env.context.get("document_type_id"),
                    "fiscal_operation_id": self.env.context.get("fiscal_operation_id"),
                    "issuer": "partner" if journal.type == "purchase" else "company",
                }
            )
            invoice = self.env["account.move"].new(invoice_dict)

            invoice_dict = invoice._convert_to_write(invoice._cache)
        return invoice_dict

    def _prepare_invoice_line(self, settlement, invoice, product):
        invoice_line_dict = super()._prepare_invoice_line(settlement, invoice, product)
        if self.env.context.get("fiscal_operation_id"):
            invoice_line_dict.update(
                {
                    "fiscal_operation_id": self.env.context.get("fiscal_operation_id"),
                }
            )
            invoice_line = self.env["account.move.line"].new(invoice_line_dict)
            invoice_line._onchange_product_id_fiscal()
            # Put commission fee after product onchange
            if invoice_line.invoice_id.type == "in_refund":
                invoice_line.price_unit = -settlement.total
            else:
                invoice_line.price_unit = settlement.total
            invoice_line._onchange_fiscal_operation_id()
            invoice_line_dict = invoice_line._convert_to_write(invoice_line._cache)
        return invoice_line_dict
