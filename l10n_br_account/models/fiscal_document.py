# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC_EM_DIGITACAO


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    move_ids = fields.One2many(
        comodel_name="account.move",
        inverse_name="fiscal_document_id",
        string="Invoices",
    )

    def modified(self, fnames, create=False, before=False):
        """
        Modifying a dummy fiscal document should not recompute
        any account.move related to the same dummy fiscal document.
        """
        if not self.document_type_id:
            return
        return super().modified(fnames, create, before)

    def _modified_triggers(self, tree, create=False):
        """
        Modifying a dummy fiscal document should not recompute
        any account.move related to the same dummy fiscal document.
        """
        if not self.document_type_id:
            return []
        return super()._modified_triggers(tree, create)

    def unlink(self):
        non_draft_documents = self.filtered(
            lambda d: d.state != SITUACAO_EDOC_EM_DIGITACAO
        )

        if non_draft_documents:
            UserError(
                _("You cannot delete a fiscal document " "which is not draft state.")
            )
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        # force creation of fiscal_document_line only when creating an AML record
        # In order not to affect the creation of the dummy document, a test was included
        # that verifies that the ACTIVE field is not False. As the main characteristic
        # of the dummy document is the ACTIVE field is False
        for values in vals_list:
            if values.get("fiscal_line_ids") and values.get("active") is not False:
                values.update({"fiscal_line_ids": False})
        return super().create(vals_list)
