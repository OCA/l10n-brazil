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


class SpedContribuicaoInss(models.Model, SpedRegistroIntermediario):
    _name = "sped.contribuicao.inss"
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
    sped_registro_s5001 = fields.Many2one(
        string='S-5001',
        comodel_name='sped.registro',
    )
    sped_registro_s1200 = fields.Many2one(
        string='S-1200',
        comodel_name='sped.registro',
    )
    sped_registro_s2399 = fields.Many2one(
        string='S-2399',
        comodel_name='sped.registro',
    )
    infocpcalc_ids = fields.One2many(
        string='Cálculo da Contribuição Previdenciária do Segurado',
        comodel_name='sped.contribuicao.inss.infocpcalc',
        inverse_name='parent_id',
    )
    ideestablot_ids = fields.One2many(
        string='Bases de Cálculo',
        comodel_name='sped.contribuicao.inss.ideestablot',
        inverse_name='parent_id',
    )

    @api.depends('sped_registro_s1200')
    def _compute_name(self):
        for registro in self:
            nome = 'S-5001'
            if registro.sped_registro_s1200:
                nome += ' ('
                nome += registro.sped_registro_s1200.display_name or ''
                nome += ')'
            registro.nome = nome

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        self.ensure_one()

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
