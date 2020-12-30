# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class InvalidateNumberWizard(models.TransientModel):
    _name = 'l10n_br_fiscal.invalidate.number.wizard'
    _description = 'Invalidate Number Wizard'
    _inherit = 'l10n_br_fiscal.base.wizard.mixin'

    invalidate_mode = fields.Selection(
        selection=[
            ('one_number', _('Only one number')),
            ('range_numbers', _('Range of numbers')),
        ],
        string='Invalidate',
        default='one_number',
    )

    number_start = fields.Integer(
        string='Initial Number',
        required=1,
    )

    number_end = fields.Integer(
        string='Final Number',
        required=1,
    )

    @api.onchange('invalidate_mode')
    def _onchange_invalidate_mode(self):
        for wizard in self:
            if (wizard.invalidate_mode == 'one_number'
                    and wizard.document_id.number):
                wizard.number_start = wizard.document_id.number
                wizard.number_end = wizard.document_id.number

    @api.multi
    def doit(self):
        for wizard in self:
            invalidate = self.env['l10n_br_fiscal.invalidate.number'].create({
                'company_id': wizard.document_id.company_id.id,
                'fiscal_document_id': wizard.document_id.id,
                'document_serie_id': wizard.document_id.document_serie_id.id,
                'number_start': wizard.document_id.number,
                'number_end': wizard.document_id.number,
            })
            invalidate.invalidate()
        self._close()
