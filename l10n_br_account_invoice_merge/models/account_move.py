# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):

    _inherit = "account.move"

    @api.model
    def _get_invoice_key_cols_out(self):
        result = super()._get_invoice_key_cols_out()
        result.append("document_type_id")
        result.append("fiscal_operation_id")
        return result

    @api.model
    def _get_invoice_key_cols_in(self):
        result = super()._get_invoice_key_cols_in()
        result.append("document_type_id")
        result.append("fiscal_operation_id")
        return result

    @api.model
    def _get_invoice_line_key_cols(self):
        result = super()._get_invoice_line_key_cols()
        result.append("document_type_id")
        result.append("fiscal_operation_id")
        result.append("fiscal_operation_line_id")
        result.append("fiscal_operation_type")
        result.append("fiscal_product_id")
        result.append("fiscal_tax_ids")
        result.append("fiscal_genre_id")
        result.append("cfop_id")
        result.append("ncm_id")
        return result

    @api.model
    def _get_first_invoice_fields(self, invoice):
        result = super()._get_first_invoice_fields(invoice)
        result["document_type_id"] = (invoice.document_type_id.id,)
        result["fiscal_operation_id"] = (invoice.fiscal_operation_id.id,)
        return result

    def do_merge(
        self, keep_references=True, date_invoice=False, remove_empty_invoice_lines=True
    ):
        result = super().do_merge(
            keep_references=keep_references,
            date_invoice=date_invoice,
            remove_empty_invoice_lines=remove_empty_invoice_lines,
        )

        domain = [("id", "in", list(result.keys()))]
        invoices = self.search(domain)

        for invoice in invoices:
            move = invoice.with_context({"check_move_validity": False})
            move.line_ids.filtered("exclude_from_invoice_tab").unlink()
            move._move_autocomplete_invoice_lines_values()

        return result
