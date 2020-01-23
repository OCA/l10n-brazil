# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# (c) 2020 ABGF - Hendrix Costa <hendrix.costa@abgf.gov.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp import api, fields, models
from openerp import exceptions, _

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

    start_period_id = fields.Many2one(
        string=u'Período Inicial',
        comodel_name='account.period',
        domain=[('special', '=', False)],
        required=True,
    )

    end_period_id = fields.Many2one(
        string=u'Período Final',
        comodel_name='account.period',
        domain=[('special', '=', False)],
        required=True,
    )

    min_wage = fields.Float(string='Min Wage', required=True)

    max_wage = fields.Float(string='Wage up to', required=True)

    rate = fields.Float(
        string='Rate (%)',
        help='Valor em percentagem. Ex.: 8% | 9%',
        required=True,
    )

    @api.onchange('year')
    def onchange_year(self):
        """
        """
        for record in self:
            if record.year:
                record.start_period_id = self.env['account.period'].\
                    find('{}-01-01'.format(record.year))
                record.end_period_id = self.env['account.period'].\
                    find('{}-12-01'.format(record.year))
            else:
                record.start_period_id = False
                record.end_period_id = False

    def find(self, date_from):
        """
        :param period_id:
        :return:
        """
        faixas_vigentes_ids = self.search([
            ('start_period_id.date_start', '<=', date_from),
            ('end_period_id.date_stop', '>=', date_from),
        ])

        return faixas_vigentes_ids

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = str(record.year).zfill(4)
            result.append((record['id'], name))
        return result

    def _compute_inss(self, BASE_INSS, date_from):
        ano = fields.Datetime.from_string(date_from).year
        tabela_vigente = self.find(date_from)

        if tabela_vigente:
            for faixa in tabela_vigente:
                if BASE_INSS < faixa.max_wage:
                    inss = Decimal(BASE_INSS)
                    inss *= Decimal(faixa.rate) / 100
                    inss = inss.quantize(Decimal('0.01'), ROUND_DOWN)
                    return inss, faixa.rate

            inss = Decimal(tabela_vigente[-1].max_wage)
            inss *= Decimal(tabela_vigente[-1].rate) / 100
            inss = inss.quantize(Decimal('0.01'), ROUND_DOWN)
            return inss, tabela_vigente[-1].rate

        else:
            raise exceptions.Warning(
                _('Tabela de INSS do ano {} Não encontrada!'.format(ano)))
