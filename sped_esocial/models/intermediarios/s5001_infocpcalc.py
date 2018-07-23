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


class SpedContribuicaoInssInfoCpCalc(models.Model):
    _name = "sped.contribuicao.inss.infocpcalc"

    parent_id = fields.Many2one(
        string='Pai',
        comodel_name='sped.contribuicao.inss',
    )
    tp_cr = fields.Char(                # infoCpCalc.tpCR
        string='Código de Receita',
    )
    vr_cp_seg = fields.Float(           # infoCpCalc.vrCpSeg
        string='Valor da Contribuição do Segurado',
        digits=[14, 2],
    )
    vr_desc_seg = fields.Float(         # infoCpCalc.vrDescSeg
        string='Valor Descontado do Segurado',
        digits=[14, 2],
    )
