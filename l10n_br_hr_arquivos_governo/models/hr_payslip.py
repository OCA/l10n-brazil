# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# Copyright 2019 ABGF - Hendrix Costa <hendrix.costa@abgf.gov.br>
# Copyright 2019 ABGF - Eder Campos Lopes <eder.campos@abgf.gov.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from pybrasil.valor.decimal import Decimal

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    sefip_id = fields.Many2one(
        comodel_name='l10n_br.hr.sefip',
        string='Sefip',
    )

    quantidade_dependente = fields.Integer(
        string=u'Quantidade de dependentes',
        help="Quantidade de dependentes que o "
             "funcionário tem naquele mes/ano.",
    )

    valor_total_dependente = fields.Float(
        string=u'Valor total de dependentes',
        help="Valor por dependente multiplicado pela quantidade de "
             "dependentes do funcionário tem naquele mes/ano.",
    )

    rendimentos_tributaveis = fields.Float(
        string=u'Rendimentos tributáveis IR (Mensal)',
        help="Valor dos rendimentos tributáveis "
             "do funcionário naquele mes/ano.",
    )

    @api.multi
    def button_update_valores_IR(self):
        """
        """
        for record in self:
            record.atualizar_valores()

    @api.multi
    def atualizar_valores(self, valor_por_dependente=0):
        """
        Função para Atualizar quantidade de dependentes e BASE de IR
        """
        self.ensure_one()

        valores = {}

        # Valor por cada dependente do funcionario
        if not valor_por_dependente:
            valor_por_dependente = \
                self.env['l10n_br.hr.income.tax.deductable.amount.family'].\
                    search([('year', '=', self.ano)], limit=1).amount or 0

        # Buscar valores de Rubricas no holerite
        RUBRICAS_CALCULO_DEPENDENTE = ['BASE_IRPF', 'INSS', 'PSS']

        for rubrica in RUBRICAS_CALCULO_DEPENDENTE:
            valores[rubrica] = self.line_ids.filtered(
                lambda x: x.code == rubrica).total or 0

        if not valores.get('BASE_IRPF'):
            return valores

        # Buscar provento que compoe BASE de imposto de renda
        provento = sum(self.line_ids.filtered(
            lambda x: x.salary_rule_id.compoe_base_IR and
                      x.salary_rule_id.category_id.code == 'PROVENTO'
        ).mapped('total')) or 0

        # Buscar Deducão que compoe BASE de imposto de renda
        deducao = sum(self.line_ids.filtered(
            lambda x: x.salary_rule_id.compoe_base_IR and
                      x.salary_rule_id.category_id.code == 'DEDUCAO'
        ).mapped('total')) or 0

        # Montar a base tribuavel de ferias
        ferias = ['FERIAS_COMPETENCIA_ATUAL', '1/3_FERIAS_COMPETENCIA_ATUAL']
        base_ferias = sum(self.line_ids.filtered(
            lambda x: x.code in ferias).mapped('total')) or 0

        # Holerites antigos utilizam o codigo antigo
        if not base_ferias:
            ferias = ['FERIAS', '1/3_FERIAS']
            base_ferias = sum(self.line_ids.filtered(
                lambda x: x.code in ferias).mapped('total')) or 0

        # Definir BASE bruta do IR
        self.rendimentos_tributaveis = provento + base_ferias - deducao

        # Buscar por rubricas de pensão
        RUBRICAS_PENSAO = [
            'PENSAO_ALIMENTICIA_PORCENTAGEM',
            'ADIANTAMENTO_PENSAO_13',
        ]
        valores['PENSAO'] = sum(self.line_ids.filtered(
            lambda x: x.code in RUBRICAS_PENSAO).mapped('total')) or 0

        # Definir o desconto total dos dependentes
        desconto_total_dependentes = \
            - valores.get('BASE_IRPF') - valores.get('INSS') \
            - valores.get('PSS') + self.rendimentos_tributaveis \
            - valores.get('PENSAO')

        # arredondadmento
        desconto_total_dependentes = Decimal(desconto_total_dependentes)

        # Com o valor total descontado da base do IR,
        # calcular a quantidade de dependentes
        if desconto_total_dependentes > 0:
            mod = desconto_total_dependentes % Decimal(valor_por_dependente)
            if not (round(mod,2) == 0):
                erro = \
                    'Erro ao calcular dependentes do funcionário(a).\n' \
                    '{}: {} - {}'.format(
                        self.id, self.employee_id.name, self.data_mes_ano)

                print(erro)

            else:
                self.quantidade_dependente = \
                    int(desconto_total_dependentes / valor_por_dependente)

                self.valor_total_dependente = \
                    self.quantidade_dependente * valor_por_dependente

        return valores
