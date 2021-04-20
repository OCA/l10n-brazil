# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class InvalidateNumberWizard(models.TransientModel):
    _name = 'l10n_br_fiscal.invalidate.number.wizard'
    _description = 'Invalidate Number Wizard'
    _inherit = 'l10n_br_fiscal.base.wizard.mixin'

    @api.multi
    def doit(self):
        for wizard in self:
            invalidate = self.env['l10n_br_fiscal.invalidate.number'].create({
                'company_id': wizard.document_id.company_id.id,
                'document_type_id': wizard.document_id.document_type_id.id,
                'document_serie_id': wizard.document_id.document_serie_id.id,
                'number_start': wizard.document_id.number,
                'number_end': wizard.document_id.number,
                'justification': wizard.justification,
            })
            invalidate._invalidate(wizard.document_id)
        self._close()
