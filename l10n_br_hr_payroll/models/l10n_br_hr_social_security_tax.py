# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# (c) 2020 ABGF - Hendrix Costa <hendrix.costa@abgf.gov.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import datetime

from openerp import api, fields, models, exceptions, _

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal, ROUND_DOWN
except ImportError:
    _logger.info('Cannot import pybrasil')


class L10nBrHrSocialTax(models.Model):
    _name = 'l10n_br.hr.social.security.tax'
    _description = 'Brazilian HR - Social Security Tax Table'
    _order = 'year desc, max_wage'

    year = fields.Char(
        string='Ano Referência',
        size=4,
        required=True,
        default=datetime.now().year,
    )

    date_start = fields.Date(
        string=u"Data de início",
    )

    date_stop = fields.Date(
        string=u"Data Final",
    )

    min_wage = fields.Float(string='Faixa Salarial de:', required=True)

    max_wage = fields.Float(string='Faixa salarial até:', required=True)

    rate = fields.Float(
        string='Alíquota (%)',
        help='Alíquota Ex.: 8% | 9%',
        required=True,
    )

    calculo_progressivo = fields.Boolean(
        string='Cálculo Progressivo?',
        help='Utilizar a Fórmula Progressiva da Aposentadoria',
    )

    @api.onchange('year')
    def onchange_year(self):
        """
        """
        for record in self:
            if record.year:
                record.date_start = '{}-01-01'.format(record.year)
                record.date_stop = '{}-12-31'.format(record.year)
            else:
                record.date_start = False
                record.date_stop = False

    def find(self, date_from):
        """
        :param period_id:
        :return:
        """
        faixas_vigentes_ids = self.search([
            ('date_start', '<=', date_from),
            ('date_stop', '>=', date_from),
        ])

        return faixas_vigentes_ids

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = str(record.year).zfill(4)
            result.append((record['id'], name))
        return result

    def forma_de_calculo_progressivo(self, tabela_vigente):
        """
        """
        return any(tabela_vigente.mapped('calculo_progressivo'))

    def _compute_inss(self, BASE_INSS, date_from):
        ano = fields.Datetime.from_string(date_from).year
        tabela_vigente = self.find(date_from)
        inss = 0

        if not tabela_vigente:
            raise exceptions.Warning(
                _('Tabela de INSS do ano {} Não encontrada!'.format(ano)))

        base_inss = Decimal(BASE_INSS)
        for faixa in tabela_vigente:

            if BASE_INSS < faixa.max_wage:
                inss += base_inss * Decimal(faixa.rate) / 100
                # inss = inss.quantize(Decimal('0.01'), ROUND_DOWN)
                return inss, faixa.rate

            else:
                # Quando for forma progressiva, acumula o valor de cada faixa
                if self.forma_de_calculo_progressivo(tabela_vigente):
                    agregado = \
                        (faixa.max_wage - faixa.min_wage) * faixa.rate / 100

                    # O INSS usa o truncamento de 2 casas decimais
                    agregado = \
                        Decimal(agregado).quantize(Decimal('0.01'), ROUND_DOWN)
                    inss += agregado
                    base_inss -= Decimal(faixa.max_wage)

        # Forma progressiva e ainda nao encontrou o teto, entao retornar
        # valor acumulado
        if self.forma_de_calculo_progressivo(tabela_vigente):
            return inss, faixa.rate

        # Forma tradicional de calculo
        inss = Decimal(tabela_vigente[-1].max_wage)
        inss *= Decimal(tabela_vigente[-1].rate) / 100
        inss = inss.quantize(Decimal('0.01'), ROUND_DOWN)
        return inss, tabela_vigente[-1].rate
