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


class SpedIrrf(models.Model, SpedRegistroIntermediario):
    _name = "sped.irrf"
    _rec_name = "nome"
    _order = "company_id, create_date DESC"

    nome = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    id_evento = fields.Char(
        string='ID do Evento',
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    trabalhador_id = fields.Many2one(
        string='Trabalhador',
        comodel_name='hr.employee',
    )
    sped_registro_s5002 = fields.Many2one(
        string='S-5002',
        comodel_name='sped.registro',
    )
    sped_registro_s1210 = fields.Many2one(
        string='S-1210',
        comodel_name='sped.registro',
    )
    vr_ded_deps = fields.Float(
        string='Deducação da Base do IR por dependentes',
        digits=[14, 2],
    )
    basesirrf_ids = fields.One2many(
        string='Informações relativas as bases de de cálculo do Trabalhador',
        comodel_name='sped.irrf.basesirrf',
        inverse_name='parent_id',
    )
    infoirrf_ids = fields.One2many(
        string='Informações relativas ao IRRF do Trabalhador e suas bases de cálculo',
        comodel_name='sped.irrf.infoirrf',
        inverse_name='parent_id',
    )

    @api.depends('sped_registro_s1210')
    def _compute_name(self):
        for registro in self:
            nome = 'S-5002'
            if registro.sped_registro_s1210:
                nome += ' ('
                nome += registro.sped_registro_s1210.display_name or ''
                nome += ')'
            registro.nome = nome

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        self.ensure_one()

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
