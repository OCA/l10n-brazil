# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_EM_DIGITACAO,
)


class FiscalDocument(models.Model):
    _inherit = 'l10n_br_fiscal.document'

    @api.multi
    def unlink(self):
        draft_documents = self.filtered(
            lambda d: d.state == SITUACAO_EDOC_EM_DIGITACAO)

        if draft_documents:
            UserError(_("You cannot delete a fiscal document "
                        "which is not draft state."))

        invoices = self.env['account.invoice'].search(
            [('fiscal_document_id', 'in', self.ids)])
        invoices.unlink()
        return super().unlink()
