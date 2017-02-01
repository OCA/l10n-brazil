# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrContract(models.Model):
    _inherit = 'hr.contract'

    vacation_control_ids = fields.One2many(
        comodel_name='hr.vacation.control',
        inverse_name='contract_id',
        string='Periodos Aquisitivos Alocados'
    )

    @api.model
    def create(self, vals):
        controle_ferias = self.env['hr.vacation.control'].create({
            'inicio_aquisitivo' : '2017-01-01',
            'fim_aquisitivo' : '2017-01-31',
        })
        hr_contract_id = super(HrContract, self).create(vals)
        hr_contract_id.vacation_control_ids = controle_ferias
        return hr_contract_id
