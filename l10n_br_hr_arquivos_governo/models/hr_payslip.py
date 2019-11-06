# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    sefip_id = fields.Many2one(
        comodel_name='l10n_br.hr.sefip',
        string='Sefip',
    )

    @api.multi
    def get_dependente(self):
        """
        """
        domain = [
            ('year', '=', self.ano),
        ]

        valor_por_dependente = self.env['l10n_br.hr.income.tax.deductable.amount.family'].\
            search(domain, limit=1).amount or 0

        RUBRICAS_CALCULO_DEPENDENTE = [
            'BRUTO',
            'BASE_IRPF',
            'INSS'
        ]

        valores, retorno = {}, {}

        for rubrica in RUBRICAS_CALCULO_DEPENDENTE:
            valores[rubrica] = self.line_ids.filtered(lambda x: x.code == rubrica).total or 0

        calculo_valor = valores.get('BRUTO') - (valores.get('BASE_IRPF') + valores.get('INSS'))

        if calculo_valor > 0:
            if not (calculo_valor % valor_por_dependente == 0):
                raise Warning(
                    'Erro ao calcular o número de dependente do funcionário(a)'
                    ' .\n{} - {}'.format(
                        self.employee_id.name, self.ano))
            else:
                retorno['quantidade_dependentes'] = calculo_valor / valor_por_dependente
                retorno['valor_por_dependente'] = valor_por_dependente
        else:
            retorno['quantidade_dependentes'] = 0
            retorno['valor_por_dependente'] = 0

        return retorno
