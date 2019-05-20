# -*- coding: utf-8 -*-
# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class HrContractLaborRegime(models.Model):
    _name = 'hr.contract.labor.regime'
    _description = u'Tipo de regime trabalhista'

    name = fields.Char(string='Labor regime')
    short_name = fields.Char(string='Short name')
    code = fields.Char(string='Code', size=1)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['short_name']:
                name = record['short_name'] + ' - ' + name
            result.append((record['id'], name))
        return result
