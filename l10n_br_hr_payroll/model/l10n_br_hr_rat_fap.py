# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models, _


class L10nBrHrRATFAP(models.Model):
    _name = 'l10n_br.hr.rat.fap'
    _description = 'Brazilian RAT/FAP Table'
    _order = 'company_id, year desc'

    company_id = fields.Many2one('res.company', _('Company'), required=True)
    year = fields.Integer(_('Year'), required=True)
    rat_rate = fields.Float(_('RAT rate'))
    fap_rate = fields.Float(_('FAP adjustment rate'))
    other_entities_rate = fields.Float(_('Other entities rate'))
    total_rate = fields.Float(_('Total rate'))

    @api.multi
    def name_get(self):
        result = []

        for record in self:
            name = str(self.year).zfill(4)
            #name += ' - R$ ' + str(self.amount).replace('.', ',')

            result.append((record['id'], name))

        return result
