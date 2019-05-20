# -*- coding: utf-8 -*-
# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class HrContractSalaryUnit(models.Model):
    _name = 'hr.contract.salary.unit'
    _description = u'Unidade de pagamento da parte fixa da remuneração'

    name = fields.Char(string='Salary unit')
    code = fields.Char(string='Code')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            # name = record['name']
            # if record['code']:
            #     name = record.code + '-' + record.name
            result.append((record['id'], record.code + ' - ' + record.name))
        return result
