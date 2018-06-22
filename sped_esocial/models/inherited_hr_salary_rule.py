# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions
from pysped.esocial import ProcessadorESocial
from openerp.exceptions import ValidationError


class HrSalaryRule(models.Model):

    _inherit = 'hr.salary.rule'
    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'Este Código e-Social já existe !'),
        ('identificador_unique', 'unique(identificador)', 'Este Identificador e-Social já existe !'),
    ]

    codigo = fields.Char(
        string='Código',
        size=30,
    )
    identificador = fields.Char(
        string='Identificador',
        size=8,
    )
    ini_valid = fields.Many2one(
        string='Válido desde',
        comodel_name='account.period',
    )
    fim_valid = fields.Many2one(
        string='Válido até',
        comodel_name='account.period',
    )
    nat_rubr = fields.Many2one(
        string='Natureza da Rubrica',
        comodel_name='sped.natureza_rubrica',
    )
    tp_rubr = fields.Selection(
        string='Tipo de Rubrica',
        selection=[
            ('1', '1-Vencimento, provento ou pensão'),
            ('2', '2-Desconto'),
            ('3', '3-Informativa'),
            ('4', '4-Informativa dedutora'),
        ],
    )
    cod_inc_cp = fields.Selection(
        string='Incidência Tributária para Previdência Social',
        selection=[
            ('0', 'Não é base de cálculo:'),
            ('1', 'Base de cálculo das contribuições sociais - Salário de Contribuição:'),
            ('3', 'Contribuição descontada do Segurado sobre salário de contribuição:'),
            ('5', 'Outros:'),
            ('9', 'Suspensão de incidência sobre Salário de Contribuição em decorrência de decisão judicial:'),
        ],
    )
    cod_inc_cp_0 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('00', '00-Não é base de cálculo'),
            ('01', '01-Não é base de cálculo em função de acordos internacionais de previdência social'),
        ]
    )
    cod_inc_cp_1 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('11', '11-Mensal'),
            ('12', '12-13º Salário'),
            ('13', '13-Exclusiva do Empregador - mensal'),
            ('14', '14-Exclusiva do Empregador - 13º salário'),
            ('15', '15-Exclusiva do segurado - mensal'),
            ('16', '16-Exclusiva do segurado - 13º salário'),
            ('21', '21-Salário maternidade mensal pago pelo Empregador'),
            ('22', '22-Salário maternidade - 13º Salário, pago pelo Empregador'),
            ('23', '23-Auxílio doença mensal - Regime Próprio de Previdência Social'),
            ('24', '24-Auxílio doença 13º salário doença - Regime próprio de previdência social'),
            ('25', '25-Salário maternidade mensal pago pelo INSS'),
            ('26', '26-Salário maternidade - 13º salário, pago pelo INSS'),
        ]
    )
    cod_inc_cp_3 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('31', '31-Mensal'),
            ('32', '32-13º Salário'),
            ('34', '34-SEST'),
            ('35', '35-SENAT'),
        ]
    )
    cod_inc_cp_5 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('51', '51-Salário-família'),
            ('61', '61-Complemento de salário-mínimo - Regime próprio de previdência social'),
        ]
    )
    cod_inc_cp_9 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('91', '91-Mensal'),
            ('92', '92-13º Salário'),
            ('93', '93-Salário maternidade'),
            ('94', '94-Salário maternidade 13º salário'),
        ]
    )
    cod_inc_irrf = fields.Selection(
        string='Incidência Tributária para o IRRF',
        selection=[
            ('0', 'Não é rendimento tributável:'),
            ('1', 'Rendimentos tributáveis - base de cálculo do IRRF:'),
            ('3', 'Retenções do IRRF efetuadas sobre:'),
            ('4', 'Deduções da base de cálculo do IRRF:'),
            ('7', 'Isenções do IRRF:'),
            ('8', 'Demandas Judiciais:'),
            ('9', 'Incidência Suspensa decorrente de decisão judicial, relativas a base de cálculo do IRRF sobre:'),
        ],
    )
    cod_inc_irrf_0 = fields.Selection(
        string='Cód.Incid.trib.IRRF',
        selection=[
            ('00', '00-Rendimento não tributável'),
            ('01', '01-Rendimento não tributável em função de acordos internacionais de bitributação'),
        ]
    )
    cod_inc_irrf_1 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('11', '11-Remuneração Mensal'),
            ('12', '12-13º Salário'),
            ('13', '13-Férias'),
            ('14', '14-PLR'),
            ('15', '15-Rendimentos Recebidos Acumuladamente - RRA'),
        ]
    )
    cod_inc_irrf_3 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('31', '31-Remuneração Mensal'),
            ('32', '32-13º Salário'),
            ('33', '33-Férias'),
            ('34', '34-PLR'),
            ('35', '35-RRA'),
        ]
    )
    cod_inc_irrf_4 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('41', '41-Previdência Social Oficial - PSO - Remuner.mensal'),
            ('42', '42-PSO - 13º salário'),
            ('43', '43-PSO - Férias'),
            ('44', '44-PSO - RRA'),
            ('46', '46-Previdência Privada - salário mensal'),
            ('47', '47-Previdência Privada - 13º salário'),
            ('51', '51-Pensão Alimentícia - Remuneração mensal'),
            ('52', '52-Pensão Alimentícia - 13º salário'),
            ('53', '53-Pensão Alimentícia - Férias'),
            ('54', '54-Pensão Alimentícia - PLR'),
            ('55', '55-Pensão Alimentícia - RRA'),
            ('61', '61-Fundo de Aposentadoria Programada Individual - FAPI - Remuneração Mensal'),
            ('62', '62-Fundo de Aposentadoria Programada Individual - FAPI - 13º Salário'),
            ('63', '63-Fundo de Previdência Complementar do Servidor Público - Funpresp - Remuneração mensal'),
            ('64', '64-Fundo de Previdência Complementar do Servidor Público - Funpresp - 13] salário'),
        ]
    )
    cod_inc_irrf_7 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('70', '70-Parcela Isenta 65 anos - Remuneração mensal'),
            ('71', '71-Parcela Isenta 65 anos - 13º salário'),
            ('72', '72-Diárias'),
            ('73', '73-Ajuda de custo'),
            ('74', '74-Indenização e rescisão de contrato, inclusive a título de PDV e acidentes de trabalho'),
            ('75', '75-Abono pecuniário'),
            ('76', '76-Pensão, aposentadoria ou reforma por moléstia grave ou acidente em serviço - Remuneração Mensal'),
            ('77', '77-Pensão, aposentadoria ou reforma por moléstia grave ou acidente em serviço - 13º salário'),
            ('78', '78-Valores pagos a titular ou sócio de microempresa ou empresa de pequeno porte, exceto pró-labore e alugueis'),
            ('79', '79-Outras isenções (o nome da rubrica deve ser claro para identificação da natureza dos valores)'),
        ]
    )
    cod_inc_irrf_8 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('81', '81-Depósito judicial'),
            ('82', '82-Compensação judicial do ano calendário'),
            ('83', '83-Compensação judicial de anos anteriores'),
        ]
    )
    cod_inc_irrf_9 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('91', '91-Remuneração mensal'),
            ('92', '92-13º Salário'),
            ('93', '93-Férias'),
            ('94', '94-PLR'),
            ('95', '95-RRA'),
        ]
    )
    cod_inc_fgts = fields.Selection(
        string='Cód.Incid.para o FGTS',
        selection=[
            ('00', '00-Não é base de cálculo do FGTS'),
            ('11', '11-Base de cálculo do FGTS'),
            ('12', '12-Base de Cálculo do FGTS 13º salário'),
            ('21', '21-Base de Cálculo do FGTS Rescisório (aviso prévio)'),
            ('91', '91-Incidência suspensa em decorrência de decisão judicial'),
        ],
    )
    cod_inc_sind = fields.Selection(
        string='Cód.Incid.para a Contr.Sindical',
        selection=[
            ('00', '00-Não é base de cálculo'),
            ('11', '11-Base de cálculo'),
            ('31', '31-Valor da contribuição sindical laboral descontada'),
            ('91', '91-Incidência suspensa em decorrência de decisão judicial'),
        ],
    )
