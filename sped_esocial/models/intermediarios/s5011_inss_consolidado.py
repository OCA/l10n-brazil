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


class SpedInssConsolidado(models.Model, SpedRegistroIntermediario):
    _name = "sped.inss.consolidado"
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
    sped_registro_s5011 = fields.Many2one(
        string='S-5011',
        comodel_name='sped.registro',
    )
    sped_registro_s1299 = fields.Many2one(
        string='S-1299',
        comodel_name='sped.registro',
    )
    ind_exist_info = fields.Selection(
        string='Existe Informação?',
        selection=[
            ('1', '1-Há informações com apuração de contribuições sociais'),
            ('2', '2-Há movimento porém sem apuração de contribuições sociais'),
            ('3', '3-Não há movimento no período informado em {perApur}'),
        ],
    )
    vr_desc_cp = fields.Float(
        string='Total da Contribuição descontada dos segurados',
        digits=[14, 2],
    )
    vr_cp_seg = fields.Float(
        string='Total calculado relativo à contribuição dos segurados',
        digits=[14, 2],
    )
    class_trib = fields.Many2one(
        string='Classificação Tributária',
        comodel_name='sped.classificacao_tributaria',
    )
    ind_coop = fields.Selection(
        string='Indicativo de Cooperativa',
        selection=[
            ('0', '0-Não é cooperativa'),
            ('1', '1-Cooperativa de Trabalho'),
            ('2', '2-Cooperativa de Produção'),
            ('3', '3-Outras Cooperativas'),
        ],
    )
    ind_constr = fields.Selection(
        string='Indicativo de Contrutora',
        selection=[
            ('0', '0-Não é Construtora'),
            ('1', '1-Empresa Construtora'),
        ],
    )
    ind_subst_patr = fields.Selection(
        string='Indicativo de substituição da contribuição previdenciária patronal',
        selection=[
            ('1', '1-Integralmente substituída'),
            ('2', '2-Parcialmente substituída'),
        ],
    )
    perc_red_contrib = fields.Float(
        string='% Redução da contribuição previsa na lei 12.546/2011',
        digits=[5, 2],
    )
    ideestab_ids = fields.One2many(
        string='Estabelecimentos/Obras de Construção Civil',
        comodel_name='sped.inss.consolidado.ideestab',
        inverse_name='parent_id',
    )

    @api.depends('sped_registro_s1299')
    def _compute_name(self):
        for registro in self:
            nome = 'S-5011'
            if registro.sped_registro_s1299:
                nome += ' ('
                nome += registro.sped_registro_s1299.display_name or ''
                nome += ')'
            registro.nome = nome

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        self.ensure_one()

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
