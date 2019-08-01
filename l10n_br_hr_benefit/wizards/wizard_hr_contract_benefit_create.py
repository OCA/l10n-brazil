# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class WizardHrContractBenefit(models.TransientModel):
    _name = 'wizard.hr.contract.benefit.create'

    old_benfit_ids = fields.Many2many(
        comodel_name='hr.contract.benefit',
        string='Benefícios Atuais',
        readonly=True,
    )
    new_benefit_ids = fields.Many2many(
        comodel_name='hr.benefit.type',
        string='Novos Benefícios',
        domain=lambda self: self._domain_benefits(),
    )

    @api.model
    def _domain_benefits(self):
        """
        Dominio para buscar os registros maiores que 01/2017
        """
        context = self.env.context

        if not (context.get('active_model') and context.get('active_id')):
            return False

        ids = self.env[context.get('active_model')].browse(
            [context.get('active_id')]
        ).benefit_ids.mapped('benefit_type_id').ids

        domain = [
            ('id', 'not in', ids),
        ]
        return domain

    @api.model
    def default_get(self, field_list):
        res = super(WizardHrContractBenefit, self).default_get(field_list)
        context = self.env.context

        if context.get('active_model') in (
                'hr.employee', 'hr.employee.dependent'
        ):
            res.update({
                'old_benfit_ids': self.env[context.get('active_model')].browse(
                    [context.get('active_id')]
                ).benefit_ids.ids
            })

        return res

    @api.multi
    def doit(self):

        for wizard in self:

            context = self.env.context

            if context.get('active_model') == 'hr.employee':
                employee_id = self.env[context.get('active_model')].browse(
                    context.get('active_id')
                )
                beneficiary_id = employee_id.address_home_id

            elif context.get('active_model') == 'hr.employee.dependent':
                dependent_id = self.env[context.get('active_model')].browse(
                    context.get('active_id')
                )
                employee_id = dependent_id.employee_id
                beneficiary_id = dependent_id.partner_id

            contract_id = self.env['hr.contract'].search(
                [('employee_id', '=', employee_id.id)], limit=1
            )

            hr_contract_benefit = self.env['hr.contract.benefit']

            for benefit in wizard.new_benefit_ids:
                hr_contract_benefit |= hr_contract_benefit.create({
                    'benefit_type_id': benefit.id,
                    'date_start': fields.Date.context_today(self),
                    'contract_id': contract_id.id,
                    'beneficiary_id': beneficiary_id.id
                })

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Beneficios Gerados',
            'res_model': 'hr.contract.benefit',
            'domain': [('id', '=', hr_contract_benefit.ids)],
            'view_mode': 'tree,form',
            'view_type': 'form',
            'view_id': False,
        }
        return action
