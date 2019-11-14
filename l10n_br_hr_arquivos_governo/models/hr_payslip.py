# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning
from pybrasil.valor.decimal import Decimal

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    sefip_id = fields.Many2one(
        comodel_name='l10n_br.hr.sefip',
        string='Sefip',
    )

    quantidade_dependente = fields.Integer(
        string=u'Quantidade de dependentes',
        help="Quantidade de dependentes que o funcionário tem naquele mes/ano.",
    )

    valor_total_dependente = fields.Float(
        string=u'Valor total de dependentes',
        help="Valor por dependente multiplicado pela quantidade de dependentes do funcionário tem naquele mes/ano.",
    )

    rendimentos_tributaveis = fields.Float(
        string=u'Valor dos rendimentos tributáveis',
        help="Valor dos rendimentos tributáveis do funcionário naquele mes/ano.",
    )

    @api.multi
    def get_dependente(self, valor_por_dependente=0):
        """
        """

        if not valor_por_dependente:
            domain = [
                ('year', '=', self.ano),
            ]

            valor_por_dependente = self.env['l10n_br.hr.income.tax.deductable.amount.family']. \
                                       search(domain, limit=1).amount or 0

        RUBRICAS_CALCULO_DEPENDENTE = [
            'BASE_IRPF',
            'INSS',
            'PSS',
        ]

        valores, retorno = {}, {}

        retorno['quantidade_dependentes'] = 0
        retorno['valor_por_dependente'] = 0
        retorno['base_ir'] = 0

        for rubrica in RUBRICAS_CALCULO_DEPENDENTE:
            valores[rubrica] = self.line_ids.filtered(
                lambda x: x.code == rubrica).total or 0

        if not valores.get('BASE_IRPF'):
            return retorno

        provento = sum(self.line_ids.filtered(
            lambda x: x.salary_rule_id.compoe_base_IR and x.salary_rule_id.category_id.code == 'PROVENTO').mapped('total')) or 0

        deducao = sum(self.line_ids.filtered(
            lambda x: x.salary_rule_id.compoe_base_IR and x.salary_rule_id.category_id.code == 'DEDUCAO').mapped(
            'total')) or 0

        valores['BASE_IR'] = provento - deducao

        valores['PENSAO'] = sum(self.line_ids.filtered(
            lambda x: x.code in ['PENSAO_ALIMENTICIA_PORCENTAGEM', 'ADIANTAMENTO_PENSAO_13']).mapped('total')) or 0

        calculo_valor = -valores.get('BASE_IRPF') \
                        - valores.get('INSS') \
                        - valores.get('PSS') \
                        + valores.get('BASE_IR') \
                        - valores.get('PENSAO')

        calculo_valor = Decimal(calculo_valor)

        if calculo_valor > 0:
            mod = calculo_valor % Decimal(valor_por_dependente)
            if not (round(mod,2) == 0):
                print('\nErro ao calcular o número de dependente do funcionário(a). '
                      '\n{}-{} - {}/{}'.format(self.id, self.employee_id.name, self.mes_do_ano2, self.ano))
            else:
                retorno['quantidade_dependentes'] = int(calculo_valor / valor_por_dependente)
                retorno['valor_por_dependente'] = round(valor_por_dependente, 2)
                retorno['base_ir'] = valores['BASE_IR']
        return retorno
