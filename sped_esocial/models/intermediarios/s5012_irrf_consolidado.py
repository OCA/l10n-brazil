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


class SpedIrrfConsolidado(models.Model, SpedRegistroIntermediario):
    _name = "sped.irrf.consolidado"
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
    sped_registro_s5012 = fields.Many2one(
        string='S-5012',
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
    infocrcontrib_ids = fields.One2many(
        string='Informações Consolidadas do IRRF por código de receita',
        comodel_name='sped.irrf.consolidado.infocrcontrib',
        inverse_name='parent_id',
    )

    @api.depends('sped_registro_s1299')
    def _compute_name(self):
        for registro in self:
            nome = 'S-5012'
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
