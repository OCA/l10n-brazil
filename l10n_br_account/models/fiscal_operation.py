# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.addons.account.models.account_invoice import TYPE2JOURNAL

FISCAL_TYPE_INVOICE = {
    'purchase': 'in_invoice',
    'purchase_refund': 'in_refund',
    'return_in': 'in_refund',
    'sale': 'out_invoice',
    'sale_refund': 'out_refund',
    'return_out': 'out_refund',
    'other': 'out_invoice',
}


class Operation(models.Model):
    _inherit = 'l10n_br_fiscal.operation'

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Account Journal',
        company_dependent=True,
        domain="[('type', 'in', {'out': ['sale', 'general'], 'in': "
               "['purchase', 'general'], 'all': ['sale', 'purchase', "
               "'general']}.get(fiscal_operation_type, []))]",
    )

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal Position',
        company_dependent=True,
    )

    @api.multi
    def _change_action_view(self, action):
        fiscal_op_type = action.get('context')
        if fiscal_op_type == 'out':
            new_action = self.env.ref(
                'l10n_br_account.fiscal_invoice_out_action')
        elif fiscal_op_type == 'in':
            new_action = self.env.ref(
                'l10n_br_account.fiscal_invoice_out_action')
        else:
            new_action = self.env.ref(
                'l10n_br_account.fiscal_invoice_all_action')
        invoice_type = FISCAL_TYPE_INVOICE[self.fiscal_type]
        journal_type = TYPE2JOURNAL[invoice_type]
        new_action['context'] = ({
            'type': invoice_type,
            'default_fiscal_operation_type': self.fiscal_type,
            'default_fiscal_operation_id': self.id,
            'journal_type': journal_type,
        })
        new_action['domain'] = action.get('domain', {})
        return new_action.read()[0]

    @api.multi
    def action_create_new(self):
        action = super().action_create_new()
        action['res_model'] = 'account.invoice'
        action['view_id'] = self.env.ref(
            'l10n_br_account.fiscal_invoice_form').id
        action['context'] = self._change_action_view(action)['context']
        return action

    @api.multi
    def open_action(self):
        action = super().open_action()
        return self._change_action_view(action)
