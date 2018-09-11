# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import \
    SpedRegistroIntermediario
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao


class SpedReinfContribuinte(models.Model, SpedRegistroIntermediario):
    _name = 'sped.efdreinf.reabertura.eventos.periodicos'
    _rec_name = "nome"
    _order = "company_id"

    nome = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    reinf_competencia_id = fields.Many2one(
        string='Competência do Reinf',
        comodel_name='sped.efdreinf',
        required=True,
    )
    sped_inclusao = fields.Many2one(
        string='Inclusão',
        comodel_name='sped.registro',
    )
    situacao = fields.Selection(
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao',
    )
    precisa_incluir = fields.Boolean(
        string='Precisa incluir dados?',
        compute='compute_precisa_enviar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('company_id')
    def _compute_name(self):
        for registro in self:
            nome = 'Contribuinte'
            if registro.company_id:
                nome += ' ('
                nome += registro.company_id.display_name or ''
                nome += ')'
            registro.nome = nome

    @api.depends('sped_inclusao')
    def compute_situacao(self):
        for contribuinte in self:
            # Popula na tabela
            contribuinte.situacao = contribuinte.sped_inclusao.situacao

    @api.depends('sped_inclusao')
    def compute_precisa_enviar(self):
        # Roda todos os registros da lista
        for contribuinte in self:
            precisa_incluir = False

            if contribuinte.situacao != '3':

                if not contribuinte.sped_inclusao or \
                        contribuinte.sped_inclusao.situacao != '4':
                    precisa_incluir = True

            contribuinte.precisa_incluir = precisa_incluir

    @api.depends('sped_inclusao')
    def compute_ultima_atualizacao(self):
        # Roda todos os registros da lista
        for contribuinte in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if contribuinte.sped_inclusao and \
                    contribuinte.sped_inclusao.situacao == '4':
                ultima_atualizacao = contribuinte.sped_inclusao.data_hora_origem

            # Popula o campo na tabela
            contribuinte.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def criar_registro(self):
        values = {
            'tipo': 'efdreinf',
            'registro': 'R-2098',
            'ambiente': self.company_id.tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtReabreEvPer',
            'origem': ('sped.efdreinf,%s' % self.reinf_competencia_id.id),
            'origem_intermediario': (
                    'sped.efdreinf.reabertura.eventos.periodicos,%s' % self.id
            ),
        }

        # Criar o registro R-2098 de inclusão, se for necessário
        if not self.sped_inclusao:
            values['operacao'] = 'I'
            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_inclusao = sped_inclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # Calcula o Período de Apuração no formato YYYY-MM
        periodo = self.periodo_id.code[3:7] + '-' + self.periodo_id.code[0:2]

        # Cria o registro
        R2098 = pysped.efdreinf.leiaute.R2098_1()

        # Popula ideEvento
        R2098.evento.ideEvento.perApur.valor = periodo
        R2098.evento.ideEvento.tpAmb.valor = ambiente
        # Processo de Emissão = Aplicativo do Contribuinte
        R2098.evento.ideEvento.procEmi.valor = '1'
        R2098.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideContri (Dados do Contribuinte)
        R2098.evento.ideContri.tpInsc.valor = '1'
        R2098.evento.ideContri.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        return R2098, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        # Fecha o Período EFD/Reinf
        self.reinf_competencia_id.situacao = '3'  # Fechado
