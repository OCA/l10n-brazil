# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp import exceptions, _
from openerp import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal, ROUND_DOWN

except ImportError:
    _logger.info('Cannot import pybrasil')


class L10nBrHrSocialTax(models.Model):
    _name = 'l10n_br.hr.social.security.tax'
    _description = 'Brazilian HR - Social Security Tax Table'
    _order = 'year desc, max_wage'

    year = fields.Integer(string='Year', required=True)
    min_wage = fields.Float(string='Min Wage', required=True)
    max_wage = fields.Float(string='Wage up to', required=True)
    rate = fields.Float(
        string='Rate (%)',
        help='Valor em percentagem. Ex.: 8% | 9%',
        required=True)

    @api.multi
    def name_get(self):
        result = []

        for record in self:
            name = str(self.year).zfill(4)
            # name += ' - ' + str(self.max_wage).replace('.', ',')
            # name += ' - ' + str(self.amount).replace('.', ',')
            result.append((record['id'], name))

        return result

    def _compute_inss(self, BASE_INSS, date_from):
        ano = fields.Datetime.from_string(date_from).year
        tabela_inss_obj = self.env['l10n_br.hr.social.security.tax']
        tabela_vigente = tabela_inss_obj.search([('year', '=', ano)])

        if tabela_vigente:
            for faixa in tabela_vigente:
                if BASE_INSS < faixa.max_wage:
                    inss = Decimal(BASE_INSS)
                    inss *= Decimal(faixa.rate) / 100
                    inss = inss.quantize(Decimal('0.01'), ROUND_DOWN)
                    return inss

            inss = Decimal(tabela_vigente[-1].max_wage)
            inss *= Decimal(tabela_vigente[-1].rate) / 100
            inss = inss.quantize(Decimal('0.01'), ROUND_DOWN)
            return inss

        else:
            raise exceptions.Warning(
                _('Tabela de INSS do ano Vigente Não encontrada!'))
            # _logger.info("Não encontrada tabelas de INSS do ano de " + ano)
