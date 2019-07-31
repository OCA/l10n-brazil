# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class WizardHrContractBenefit(models.TransientModel):
    _name = 'wizard.hr.contract.benefit.periodic'

    period_id = fields.Many2one(
        comodel_name='account.period',
        string='Period',
    )

    @api.multi
    def doit(self):

        for wizard in self:
            active_ids = self.env.context.get('active_ids')
            hr_contract_benefit_ids = self.env['hr.contract.benefit'].browse(
                active_ids
            )
            result_ids = hr_contract_benefit_ids.gerar_prestacao_contas(
                wizard.period_id
            )

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Apuração de {}'.format(wizard.period_id.name or
                                            wizard.period_id.find().name),
            'res_model': 'hr.contract.benefit.line',
            'domain': [('id', 'in', result_ids.ids)],
            'view_mode': 'tree,form',
            'view_type': 'form',
            'view_id': False,
        }
        return action
