# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from datetime import datetime
import pysped


class SpedContribuicaoInssIdeEstabLot(models.Model):
    _name = "sped.contribuicao.inss.ideestablot"

    parent_id = fields.Many2one(
        string='Pai',
        comodel_name='sped.contribuicao.inss',
    )
    tp_insc = fields.Selection(                # ideEstabLot.tpCR
        string='Tipo',
        selection=[
            ('1', '1-CNPJ'),
            ('2', '2-CPF'),
            ('3', '3-???'),
            ('4', '4-???'),
        ],
    )
    nr_insc = fields.Char(               # infoCpCalc.vrCpSeg
        string='Inscrição',
    )
    cod_lotacao = fields.Char(         # infoCpCalc.vrDescSeg
        string='Lotação Tributária',
    )

    # infoCategIncid
    matricula = fields.Char(
        string='Matrícula do Trabalhador',
    )
    cod_categ = fields.Char(
        string='Categoria do Trabalhador',
    )
    ind_simples = fields.Selection(
        string='Indicador de Contribuição Substituída',
        selection=[
            ('1', '1-Contribuição Substituída Integralmente'),
            ('2', '2-Contribuição não substituída'),
            ('3', '3-Contribuição não substituída concomitante com contribuição substituída'),
        ],
    )

    # infoBaseCS
    ind13 = fields.Selection(
        string='Indicativo de 13º salário',
        selection=[
            ('0', '0-Mensal'),
            ('1', '1-13º Salário'),
        ],
    )
    tp_valor = fields.Selection(
        string='Tipo de valor que influi na apuração da contribução devida',
        selection=[
            ('11', '11-Base de cálculo da Contribuição Previdenciária normal'),
            ('12', '12-Base de cálculo da Contribuição Previdenciária adicional para o financiamento dos benefícios de aposentadoria especial após 15 anos de contribuição'),
            ('13', '13-Base de cálculo da Contribuição Previdenciária adicional para o financiamento dos benefícios de aposentadoria especial após 20 anos de contribuição'),
            ('14', '14-Base de cálculo da Contribuição Previdenciária adicional para o financiamento dos benefícios de aposentadoria especial após 25 anos de contribuição'),
            ('15', '15-Base de cálculo da Contribuição Previdenciária adicional normal - exclusiva do empregador'),
            ('16', '16-Base de cálculo da Contribuição Previdenciária adicional para o financiamento dos benefícios de aposentadoria especial após 15 anos de contribuição - exclusiva do empregador'),
            ('17', '17-Base de cálculo da Contribuição Previdenciária adicional para o financiamento dos benefícios de aposentadoria especial após 20 anos de contribuição - exclusiva do empregador'),
            ('18', '18-Base de cálculo da Contribuição Previdenciária adicional para o financiamento dos benefícios de aposentadoria especial após 25 anos de contribuição - exclusiva do empregador'),
            ('19', '19-Base de cálculo da Contribuição Previdenciária exclusiva do empregador'),
            ('21', '21-Valor total descontado do trabalhador para recolhimento à Previdência Social'),
            ('22', '22-valor descontado do trabalhador para recolhimento ao Sest'),
            ('23', '23-Valor descontato do trabalhador para recolhimento ao Senat'),
            ('31', '31-Valor pago ao trabalhador a título de salário-família'),
            ('32', '32-Valor pago ao trabalhados a tídulo de salário-maternidade'),
            ('91', '91-Incidência suspensa em decorrência de decisão judicial - Base de cálculo (BC) da Contribuição Previdenciária (CP) Normal'),
            ('92', '92-Incid.suspensa em decorrência de decisão judicial - BC CP Aposentadoria Especial aos 15 anos de trabalho'),
            ('93', '93-Incid.suspensa em decorrência de decisão judicial - BC CP Aposentadoria Especial aos 20 anos de trabalho'),
            ('94', '94-Incid.suspensa em decorrência de decisão judicial - BC CP Aposentadoria Especial aos 25 anos de trabalho'),
            ('95', '95-Incid.suspensa em decorrência de decisão judicial - BC CP normal - Exclusiva do empregador'),
            ('96', '96-Incid.suspensa em decorrência de decisão judicial - BC Aposentadoria Especial aos 15 anos de trabalho - Exclusiva do empregador'),
            ('97', '97-Incid.suspensa em decorrência de decisão judicial - BC Aposentadoria Especial aos 20 anos de trabalho - Exclusiva do empregador'),
            ('98', '98-Incid.suspensa em decorrência de decisão judicial - BC Aposentadoria Especial aos 25 anos de trabalho - Exclusiva do empregador'),
        ],
    )
    valor = fields.Float(
        string='Base de Cálculo',
        help='Valor da base de cálculo, dedução ou desconto da contribuição social devida à Previdência' \
             'Social ou a Outrs Entidades e Fundos, conforme definido no campo {tpValor}.',
        digits=[14, 2],
    )
