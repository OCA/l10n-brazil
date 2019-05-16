# -*- coding: utf-8 -*-
# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class HrContractResignationCause(models.Model):
    _name = 'hr.contract.resignation.cause'

    name = fields.Char(string='Resignation cause')
    code = fields.Char(string='Resignation cause code')
    fgts_withdraw_code = fields.Char(string='FGTS withdrawal code')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result
