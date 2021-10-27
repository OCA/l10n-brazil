# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, models, fields
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_EM_DIGITACAO,
)


class FiscalDocument(models.Model):
    _inherit = 'l10n_br_fiscal.document'

    invoice_ids = fields.One2many(
        comodel_name='account.invoice',
        inverse_name='fiscal_document_id',
        string="Invoices",
    )

    def unlink(self):
        non_draft_documents = self.filtered(
            lambda d: d.state != SITUACAO_EDOC_EM_DIGITACAO)

        if non_draft_documents:
            UserError(_("You cannot delete a fiscal document "
                        "which is not draft state."))
        return super().unlink()
