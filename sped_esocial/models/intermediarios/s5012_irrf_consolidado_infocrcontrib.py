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


class SpedIrrfConsolidadoInfocrcontrib(models.Model):
    _name = "sped.irrf.consolidado.infocrcontrib"
    _order = "tp_cr"

    parent_id = fields.Many2one(
        string='Pai',
        comodel_name='sped.irrf.consolidado',
    )
    tp_cr = fields.Char(
        string='Código de Receita',
    )
    vr_cr = fields.Float(
        string='Valor',
        digits=[14, 2],
    )
