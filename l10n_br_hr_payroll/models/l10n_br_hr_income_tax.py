# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal

except ImportError:
    _logger.info('Cannot import pybrasil')


class L10nBrHrIncomeTax(models.Model):
    _name = 'l10n_br.hr.income.tax'
    _description = 'Brazilian HR - Income Tax Table'
    _order = 'year desc, max_wage'

    year = fields.Integer('Year', required=True)
    max_wage = fields.Float('Wage up to', required=True)
    rate = fields.Float('Rate', required=True)
    deductable = fields.Float('Deductible amount', required=True)

    @api.multi
    def name_get(self):
        result = []

        for record in self:
            name = str(self.year).zfill(4)
            # name += ' - ' + str(self.max_wage).replace('.', ',')
            # name += ' - ' + str(self.amount).replace('.', ',')

            result.append((record['id'], name))

        return result

    @api.multi
    def _compute_irrf(self, BASE_IRRF, employee_id, inss, date_from):
        ano = fields.Datetime.from_string(date_from).year
        tabela_irrf_obj = self.env['l10n_br.hr.income.tax']
        tabela_vigente = tabela_irrf_obj.search(
            [('year', '=', ano)], order='rate DESC'
        )

        if tabela_vigente:
            for faixa in tabela_vigente:
                if BASE_IRRF > faixa.max_wage:
                    irrf = \
                        Decimal(BASE_IRRF or 0) * (
                            Decimal(faixa.rate) / 100.00
                        ) - Decimal(faixa.deductable)
                    irrf = irrf.quantize(Decimal('0.01'))
                    return irrf, faixa.rate
        else:
            raise UserError(
                _('Tabela de IRRF do ano Vigente Não encontrada!')
            )
