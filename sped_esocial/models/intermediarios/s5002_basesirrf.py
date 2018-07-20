# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from .sped_registro_intermediario import SpedRegistroIntermediario

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from datetime import datetime
import pysped


class SpedIrrfBasesirrf(models.Model):
    _name = "sped.irrf.basesirrf"

    parent_id = fields.Many2one(
        string='Pai',
        comodel_name='sped.irrf',
    )
    cod_categ = fields.Char(                # infoIrrf.codCated
        string='Código da Categoria do Trabalhador',
    )
    ind_res_br = fields.Selection(          # infoIrrf.indResBr
        string='Benef. é residente fiscal no Brasil',
        selection=[
            ('S', 'S-Sim'),
            ('N', 'N-Não'),
        ],
    )
    tp_valor = fields.Selection(            # infoIrrf.basesIrrf.tpValor
        string='Tipo de valor relativo aos rendimentos pagos e ao IRRF retido',
        selection=[

            # Rendimentos não tributáveis
            ('00', '00-Rendimento não tributável'),
            ('01', '01-Rendimento não tributável em função de acordos internacionais de bitributação'),
            ('09', '09-Outras verbas não consideradas como base de cálculo ou rendimento'),

            # Rendimentos tributáveis - base de calculo do IRRF
            ('11', '11-(Base de cálculo do IRRF:) Remuneração Mensal'),
            ('12', '12-(Base de cálculo do IRRF:) 13º Salário'),
            ('13', '13-(Base de cálculo do IRRF:) Férias'),
            ('14', '14-(Base de cálculo do IRRF:) PLR'),
            ('15', '15-(Base de cálculo do IRRF:) Rendimentos Recebidos Acumuladamente - RRA'),

            # Retenções do IRRF efetuadas sobre:
            ('31', '31-(Retenções do IRRF sobre:) Remuneração Mensal'),
            ('32', '32-(Retenções do IRRF sobre:) 13º Salário'),
            ('33', '33-(Retenções do IRRF sobre:) Férias'),
            ('34', '34-(Retenções do IRRF sobre:) PLR'),
            ('35', '35-(Retenções do IRRF sobre:) RRA'),

            # Deduções da base de cálculo do IRRF:
            ('41', '41-(Deduções da base do IRRF:) PSO - Remuneração Mensal)'),
            ('42', '42-(Deduções da base do IRRF:) PSO - 13º Salário)'),
            ('43', '43-(Deduções da base do IRRF:) PSO - Férias)'),
            ('44', '44-(Deduções da base do IRRF:) PSO - RRA)'),
            ('46', '46-(Deduções da base do IRRF:) Prev.Privada - Salário Mensal)'),
            ('47', '47-(Deduções da base do IRRF:) Prev.Privada - 13º Salário)'),
            ('51', '51-(Deduções da base do IRRF:) Pensão Alimentícia - Remuneração Mensal)'),
            ('52', '52-(Deduções da base do IRRF:) Pensão Alimentícia - 13º Salário)'),
            ('53', '53-(Deduções da base do IRRF:) Pensão Alimentícia - Férias)'),
            ('54', '54-(Deduções da base do IRRF:) Pensão Alimentícia - PLR)'),
            ('55', '55-(Deduções da base do IRRF:) Pensão Alimentícia - RRA)'),
            ('61', '61-(Deduções da base do IRRF:) FAPI - Remuneração Mensal)'),
            ('62', '62-(Deduções da base do IRRF:) FAPI - 13º Salário)'),
            ('63', '63-(Deduções da base do IRRF:) FUNPRESP - Remuneração Mensal)'),
            ('64', '64-(Deduções da base do IRRF:) FUNPRESP - 13º Salário)'),

            # Isenções do IRRF
            ('70', '70-(Isenções do IRRF:) Parcela Isenta 65 anos - Remuneração Mensal'),
            ('71', '71-(Isenções do IRRF:) Parcela Isenta 65 anos - 13º Salário'),
            ('72', '72-(Isenções do IRRF:) Diárias'),
            ('73', '73-(Isenções do IRRF:) Ajuda de Custo'),
            ('74', '74-(Isenções do IRRF:) Indenização e rescisão de contrato, inclusive a título de PDV e acidentes de trabalho'),
            ('75', '75-(Isenções do IRRF:) Abono Pecuniário'),
            ('76', '76-(Isenções do IRRF:) Pensão, aposentadoria ou reforma por moléstia grave ou acidente em serviço - Remuneração Mensal'),
            ('77', '77-(Isenções do IRRF:) Pensão, aposentadoria ou reforma por moléstia grave ou acidente em serviço - 13º Salário'),
            ('78', '78-(Isenções do IRRF:) Valores pagos a titular ou sócio de microempresa ou empresa de pequeno port, exceto pró-labore e alugueis'),
            ('79', '79-(Isenções do IRRF:) Outras Isenções (identificar o nome da rubrica em S-1010)'),

            # Demandas Judiciais
            ('81', '81-(Demandas Judiciais:) Depósito Judicial'),
            ('82', '82-(Compensação Judicial do ano calendário'),
            ('83', '83-(Compensação Judicial de anos anteriores'),

            # Incidência Suspensa decorrente de decisão judicial, relativas a base de cálculo do IRRF sobre:
            ('91', '91-(Incid.Susp.Dec.Jud.base do IRRF:) Remuneração Mensal'),
            ('92', '92-(Incid.Susp.Dec.Jud.base do IRRF:) 13º Salário'),
            ('93', '93-(Incid.Susp.Dec.Jud.base do IRRF:) Férias'),
            ('94', '94-(Incid.Susp.Dec.Jud.base do IRRF:) PLR'),
            ('95', '95-(Incid.Susp.Dec.Jud.base do IRRF:) RRA'),
        ],
    )
    valor = fields.Float(
        string='Valor',
        digits=[14, 2],
    )
