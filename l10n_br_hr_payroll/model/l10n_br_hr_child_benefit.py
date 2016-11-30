# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models, _


class L10nBrHrChildBenefit(models.Model):
    _name = 'l10n_br.hr.child.benefit'
    _description = 'Brazilian HR - Child Benefit Table'
    _order = 'year desc, max_wage'

    year = fields.Integer(_('Year'), required=True)
    max_wage = fields.Float(_('Wage up to'), required=True)
    amount = fields.Float(_('Amount per child'), required=True)

    @api.multi
    def name_get(self):
        result = []

        for record in self:
            name = str(self.year).zfill(4)
            #name += ' - ' + str(self.max_wage).replace('.', ',')
            #name += ' - ' + str(self.amount).replace('.', ',')

            result.append((record['id'], name))

        return result
