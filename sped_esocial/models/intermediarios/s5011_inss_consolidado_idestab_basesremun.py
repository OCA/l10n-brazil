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


class SpedInssConsolidadoIdestabBasesremun(models.Model):
    _name = "sped.inss.consolidado.basesremun"
    _order = "cod_categ, ind_incid"

    parent_id = fields.Many2one(
        string='Pai',
        comodel_name='sped.inss.consolidado.ideestab',
    )
    ind_incid = fields.Selection(
        string='Tipo de incidência',
        selection=[
            ('1', '1-Normal'),
            ('2', '2-Ativ.Concomitante'),
            ('9', '9-Substituída ou Isenta'),
        ],
    )
    cod_categ = fields.Many2one(
        string='Categoria Trabalhador',
        comodel_name='sped.categoria_trabalhador',
    )
    vr_bc_cp_00 = fields.Float(
        string='vrBcCp00',
        digits=[14, 2],
    )
    vr_bc_cp_15 = fields.Float(
        string='vrBcCp15',
        digits=[14, 2],
    )
    vr_bc_cp_20 = fields.Float(
        string='vrBcCp20',
        digits=[14, 2],
    )
    vr_bc_cp_25 = fields.Float(
        string='vrBcCp25',
        digits=[14, 2],
    )
    vr_susp_bc_cp_00 = fields.Float(
        string='vrSuspBcCp00',
        digits=[14, 2],
    )
    vr_susp_bc_cp_15 = fields.Float(
        string='vrSuspBcCp15',
        digits=[14, 2],
    )
    vr_susp_bc_cp_20 = fields.Float(
        string='vrSuspBcCp20',
        digits=[14, 2],
    )
    vr_susp_bc_cp_25 = fields.Float(
        string='vrSuspBcCp25',
        digits=[14, 2],
    )
    vr_desc_sest = fields.Float(
        string='vrDescSest',
        digits=[14, 2],
    )
    vr_calc_sest = fields.Float(
        string='vrCalcSest',
        digits=[14, 2],
    )
    vr_desc_senat = fields.Float(
        string='vrDescSenat',
        digits=[14, 2],
    )
    vr_calc_senat = fields.Float(
        string='vrCalcSenat',
        digits=[14, 2],
    )
    vr_sal_fam = fields.Float(
        string='vrSalFam',
        digits=[14, 2],
    )
    vr_sal_mat = fields.Float(
        string='vrSalMat',
        digits=[14, 2],
    )
