# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BaseWizardMixin(models.TransientModel):
    _name = 'l10n_br_fiscal.base.wizard.mixin'
    _description = 'Fiscal Base Wizard Mixin'

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Fiscal Document',
    )

    document_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.type',
        string='Document Type',
    )

    event_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.event',
        string='Fiscal Event',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )

    justification = fields.Text(
        string='Justification',
        size=255,
        required=True,
    )

    state = fields.Selection(
        selection=[
            ('init', 'init'),
            ('confirm', 'confirm'),
            ('done', 'done')
        ],
        string='State',
        readonly=True,
        default='init',
    )

    @api.model
    def default_get(self, fields_list):
        default_values = super().default_get(fields_list)
        active_model = self.env.context['active_model']
        active_id = self.env.context['active_id']

        key_field = {
            'l10n_br_fiscal.document': 'document_id',
            'res.partner': 'partner_id',
        }

        default_values.update({key_field[active_model]: active_id})
        return default_values

    @api.multi
    def button_back(self):
        self.ensure_one()
        self.state = 'init'
        return self._reopen()

    @api.multi
    def _reopen(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
            'nodestroy': True
        }
