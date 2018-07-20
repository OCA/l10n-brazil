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


class SpedIrrfInfoirrf(models.Model):
    _name = "sped.irrf.infoirrf"

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
    tp_cr = fields.Selection(
        string='Código de Receita',
        selection=[
            ('047301', '0473-01 - Renda e Proventos de Qualquer Natureza'),
            ('056107', '0561-01 - IRRF - Rendimento do Trabalho Assalariado no País/Ausente no Exterior a Serviço do País'),
            ('056108', '0561-08 - IRRF - Empregado Doméstico'),
            ('056109', '0561-09 - IRRF - Empregado Doméstico - 13º Sal. Rescisão'),
            ('056110', '0561-10 - IRRF - Empregado Doméstico - 13º salário'),
            ('056111', '0561-11 - IRRF - Empregado/Trabalhador Rural - Segurado Especial'),
            ('056112', '0561-12 - IRRF - Empregado/Trabalhador Rural - Segurado Especial 13º salário'),
            ('056113', '0561-13 - IRRF - Empregado/Trabalhador Rural - Segurado Especial 13º salário rescisório'),
            ('058806', '0588-06 - IRRF - Rendimento do trabalho sem vínculo empregatício'),
            ('061001', '0610-01 - IRRF - Rendimentos relativos a prestação de serviços de transporte rodoviário internacional de carga, pagos a transportador autônomo PF residente no Paraguai'),
            ('328006', '3280-06 - IRRF - Serviços Prestados por associados de cooperativas de trabalho'),
            ('3533',   '3533 - Proventos de Aposentadoria, Reserva, Reforma ou Pensão Pagos por Previdência Púbrica'),
            ('356201', '3562-01 - IRRF - Participação dos trabalhadores em Lucros ou Resultados (PLR)'),
        ],
    )
    vr_irrf_desc = fields.Float(
        string='Valor do IRRF Descontado',
        digits=[14, 2],
    )
