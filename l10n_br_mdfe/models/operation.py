# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MDFeOperation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    def action_create_new(self):
        result = super().action_create_new()
        doc_type_id = result["context"].get("default_document_type_id")
        if doc_type_id:
            doc_type = self.env["l10n_br_fiscal.document.type"].browse(doc_type_id)
            if doc_type.code == "58" and not result["context"].get(
                "default_document_serie_id"
            ):
                company = self.env.company
                fiscal_op = self.env["l10n_br_fiscal.operation"].browse(
                    result["context"].get("default_fiscal_operation_id")
                )
                serie = doc_type.get_document_serie(company, fiscal_op)
                if not serie:
                    serie = doc_type._get_default_document_serie(company)
                if serie:
                    result["context"]["default_document_serie_id"] = serie.id
        return result
