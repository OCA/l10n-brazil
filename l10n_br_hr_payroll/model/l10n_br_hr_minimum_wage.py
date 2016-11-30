# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models, _


class L10nBrHrMinimumWage(models.Model):
    _name = 'l10n_br.hr.minimum.wage'
    _description = 'Brazilian HR - Minimum Wage Table'
    _order = 'year desc'

    year = fields.Integer(_('Year'), required=True)
    amount = fields.Float(_('Amount'), required=True)

    @api.multi
    def name_get(self):
        result = []

        for record in self:
            name = str(self.year).zfill(4)
            #name += ' - R$ ' + str(self.amount).replace('.', ',')

            result.append((record['id'], name))

        return result
