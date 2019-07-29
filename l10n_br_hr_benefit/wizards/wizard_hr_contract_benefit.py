# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class WizardHrContractBenefit(models.TransientModel):
    _name = 'wizard.hr.contract.benefit'

    old_benfit_ids = fields.Many2many(
        comodel_name='hr.benefit.type',
        string='Beneficios Atuais',
    )
    new_benefit_ids = fields.Many2many(
        comodel_name='hr.benefit.type',
        string='Novos Beneficios',
    )

    @api.multi
    def doit(self):
        for wizard in self:
            # TODO
            pass
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Action Name',  # TODO
            'res_model': 'result.model',  # TODO
            'domain': [('id', '=', result_ids)],  # TODO
            'view_mode': 'form,tree',
        }
        return action
