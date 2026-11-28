# Copyright 2026 - TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class FiscalDocument(models.Model):
    """Refresh the DF-e inbox link when this document's identity changes."""

    _inherit = "l10n_br_fiscal.document"

    def _invalidate_dfe_inbox_link(self):
        """Drop the cached inbox link for these access keys.

        ``fiscal_document_id`` on the inbox depends only on the inbox key, so
        a document created after that field was read stays invisible until
        the cache is cleared.
        """
        keys = set()
        for key in self.mapped("document_key"):
            if not key:
                continue
            keys.add(key)
            compact = key.replace(" ", "")
            if compact:
                keys.add(compact)
        if not keys:
            return
        inbox = self.env["l10n_br_fiscal_dfe.document"].search(
            [("access_key", "in", list(keys))]
        )
        if inbox:
            inbox.invalidate_recordset(["fiscal_document_id"])

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._invalidate_dfe_inbox_link()
        return records

    def write(self, vals):
        watched = {"document_key", "imported_document", "company_id"}
        if watched.intersection(vals):
            self._invalidate_dfe_inbox_link()
        result = super().write(vals)
        if watched.intersection(vals):
            self._invalidate_dfe_inbox_link()
        return result

    def unlink(self):
        self._invalidate_dfe_inbox_link()
        return super().unlink()
