# Copyright (C) 2023 - TODAY Renan Hiroki Bastos - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    @api.model_create_multi
    def create(self, vals_list):
        if self._context.get("create_from_move_line") and self._context.get(
            "create_from_document"
        ):
            return []
        else:
            documents = super().create(vals_list)
        return documents
