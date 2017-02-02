# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from dateutil.relativedelta import relativedelta


class HrContract(models.Model):
    _inherit = 'hr.contract'

    vacation_control_ids = fields.One2many(
        comodel_name='hr.vacation.control',
        inverse_name='contract_id',
        string='Periodos Aquisitivos Alocados'
    )

    @api.model
    def create(self, vals):
        inicio_aquisitivo = vals['date_start']
        fim_aquisitivo = fields.Date.from_string(inicio_aquisitivo) + relativedelta(years=1) + relativedelta(days=-1)
        inicio_concessivo =  fim_aquisitivo + relativedelta(days=1)
        fim_concessivo = inicio_concessivo + relativedelta(years=1) + relativedelta(days=-1)
        controle_ferias = self.env['hr.vacation.control'].create({
            'inicio_aquisitivo' : inicio_aquisitivo,
            'fim_aquisitivo' : fim_aquisitivo,
            'inicio_concessivo': inicio_concessivo,
            'fim_concessivo': fim_concessivo,
        })
        hr_contract_id = super(HrContract, self).create(vals)
        hr_contract_id.vacation_control_ids = controle_ferias
        return hr_contract_id
