# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    @api.depends("city_taxation_code_id")
    def _compute_issqn_fg_city_id(self):
        """Keep the incidence city parsed from an imported national NFS-e.

        The standard compute falls back to the company city when the line has
        no municipal taxation code. That city is not the ``cLocIncid`` of the
        note, so an imported national NFS-e keeps the value written from the XML.
        """
        imported = self.filtered(
            lambda line: line.document_id.imported_document
            and line.document_id._is_national_nfse_key()
        )
        return super(DocumentLine, self - imported)._compute_issqn_fg_city_id()
