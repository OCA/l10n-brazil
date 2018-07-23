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


class SpedInssConsolidadoIdestab(models.Model):
    _name = "sped.inss.consolidado.ideestab"
    _order = "estabelecimento_id"

    parent_id = fields.Many2one(
        string='Pai',
        comodel_name='sped.inss.consolidado',
    )
    estabelecimento_id = fields.Many2one(
        string='Estabelecimento',
        comodel_name='res.company',
    )
    cnae_prep = fields.Char(
        string='CNAE',
    )
    aliq_rat = fields.Float(
        string='Alíquota RAT',
        digits=[1, 0],
    )
    fap = fields.Float(
        string='FAP',
        digits=[5, 4],
    )
    aliq_rat_ajust = fields.Float(
        string='% RAT ajust.pelo FAP',
        digits=[5, 4],
    )
    lotacao_id = fields.Many2one(
        string='Lotação Tributária',
        comodel_name='res.company',
    )
    fpas_id = fields.Many2one(
        string='FPAS',
        comodel_name='sped.codigo_aliquota',
    )
    cod_tercs = fields.Char(
        string='Código de Terceiros',
        size=4,
    )
    base_ids = fields.One2many(
        string='Bases de Cálculo',
        comodel_name='sped.inss.consolidado.basesremun',
        inverse_name='parent_id',
    )
