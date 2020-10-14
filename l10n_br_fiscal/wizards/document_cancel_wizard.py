# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models


class DocumentCancelWizard(models.TransientModel):
    _name = 'l10n_br_fiscal.document.cancel.wizard'
    _description = 'Fiscal Document Cancel Wizard'
    _inherit = 'l10n_br_fiscal.base.wizard.mixin'

    @api.multi
    def doit(self):
        for wiz in self:
            if wiz.document_id:
                message = _("Cancellation: {}").format(wiz.justification)
                wiz.document_id.with_context(message=message)._document_cancel()
        return {'type': 'ir.actions.act_window_close'}
