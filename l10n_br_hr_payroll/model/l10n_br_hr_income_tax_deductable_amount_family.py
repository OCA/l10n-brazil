# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models, _


class L10nBrHrIncomeTaxDeductableAmountFamily(models.Model):
    _name = 'l10n_br.hr.income.tax.deductable.amount.family'
    _description = 'Brazilian HR - Income Tax - Deductable Amount per Family Member Table'
    _order = 'year desc'

    year = fields.Integer(_('Year'), required=True)
    amount = fields.Float(_('Deductable amount'), required=True)

    @api.multi
    def name_get(self):
        result = []

        for record in self:
            name = str(self.year).zfill(4)
            #name += ' - ' + str(self.max_wage).replace('.', ',')
            #name += ' - ' + str(self.amount).replace('.', ',')

            result.append((record['id'], name))

        return result
