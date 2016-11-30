# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class L10nBrHrIncomeTax(models.Model):
    _name = 'l10n_br.hr.income.tax'
    _description = 'Brazilian HR - Income Tax Table'
    _order = 'year desc, max_wage'

    year = fields.Integer('Year', required=True)
    max_wage = fields.Float('Wage up to', required=True)
    rate = fields.Float('Rate', required=True)
    deductable = fields.Float('Deductable amount', required=True)

    @api.multi
    def name_get(self):
        result = []

        for record in self:
            name = str(self.year).zfill(4)
            # name += ' - ' + str(self.max_wage).replace('.', ',')
            # name += ' - ' + str(self.amount).replace('.', ',')

            result.append((record['id'], name))

        return result
