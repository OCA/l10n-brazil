# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class DocumentImportWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.import.wizard"

    def _import_edoc(self):
        binding, document = super()._import_edoc()
        dfe_document = self.env["l10n_br_fiscal_dfe.document"].search(
            [("access_key", "=", document.document_key)], limit=1
        )
        if dfe_document:
            # sudo: l10n_br_fiscal.group_user only has read access on DF-e
            dfe_document.sudo().fiscal_document_id = document
        return binding, document
