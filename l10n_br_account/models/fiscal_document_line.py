# Copyright (C) 2021 - TODAY Gabriel Cardoso de Faria - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    account_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="fiscal_document_line_id",
        string="Invoice Lines",
    )

    def modified(self, fnames, create=False, before=False):
        """
        Modifying a dummy fiscal document line should not recompute
        any account.move.line related to the same dummy fiscal document line.
        """
        if not self.document_id.document_type_id:
            return
        return super().modified(fnames, create, before)

    def _modified_triggers(self, tree, create=False):
        """
        Modifying a dummy fiscal document line should not recompute
        any account.move.line related to the same dummy fiscal document line.
        """
        if not self.document_id.document_type_id:
            return []
        return super()._modified_triggers(tree, create)
