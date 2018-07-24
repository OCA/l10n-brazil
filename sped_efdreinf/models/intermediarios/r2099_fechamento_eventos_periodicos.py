# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import \
    SpedRegistroIntermediario
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao


class SpedReinfContribuinte(models.Model, SpedRegistroIntermediario):
    _name = 'sped.efdreinf.fechamento.eventos.periodicos'
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

            # Inicia as variáveis como False
            precisa_incluir = False
            precisa_atualizar = False
            precisa_excluir = False

            # Se a situação for '3' (Aguardando Transmissão) fica tudo falso
            if self.situacao != '3':

                # Se a empresa matriz tem um período inicial definido e não tem um registro S1000 de inclusão
                # confirmado, então precisa incluir
                if contribuinte.company_id.esocial_periodo_inicial_id:
                    if not contribuinte.sped_inclusao or contribuinte.sped_inclusao.situacao != '4':
                        precisa_incluir = True

            # Popula os campos na tabela
            contribuinte.precisa_incluir = precisa_incluir

    @api.depends('sped_inclusao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for contribuinte in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if contribuinte.sped_inclusao and contribuinte.sped_inclusao.situacao == '4':
                ultima_atualizacao = contribuinte.sped_inclusao.data_hora_origem

            # Popula o campo na tabela
            contribuinte.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def criar_registro(self):
        values = {
            'tipo': 'efdreinf',
            'registro': 'R-2099',
            'ambiente': self.company_id.tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtFechaEvPer',
            'origem': ('sped.efdreinf,%s' % self.reinf_competencia_id.id),
            'origem_intermediario': (
                    'sped.efdreinf.fechamento.eventos.periodicos,%s' % self.id
            ),
        }

        # Criar o registro R-2099 de inclusão, se for necessário
        if self.precisa_incluir:
            values['operacao'] = 'I'
            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_inclusao = sped_inclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        # Calcula o Período de Apuração no formato YYYY-MM
        periodo = self.periodo_id.code[3:7] + '-' + self.periodo_id.code[0:2]

        # Cria o registro
        R2099 = pysped.efdreinf.leiaute.R2099_1()

        # Popula ideEvento
        R2099.evento.ideEvento.perApur.valor = periodo
        R2099.evento.ideEvento.tpAmb.valor = ambiente
        # Processo de Emissão = Aplicativo do Contribuinte
        R2099.evento.ideEvento.procEmi.valor = '1'
        R2099.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideContri (Dados do Contribuinte)
        R2099.evento.ideContri.tpInsc.valor = '1'
        R2099.evento.ideContri.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula ideRespInf
        R2099.evento.ideRespInf.nmResp.valor = self.company_id.nmctt
        R2099.evento.ideRespInf.cpfResp.valor = self.company_id.cpfctt
        if self.company_id.cttfonefixo:
            R2099.evento.ideRespInf.telefone.valor = self.company_id.cttfonefixo
        if self.company_id.cttemail:
            R2099.evento.ideRespInf.email.valor = self.company_id.cttemail

        # Popula infoFech
        R2099.evento.infoFech.evtServTm.valor = 'S' if self.reinf_competencia_id.evt_serv_tm else 'N'
        R2099.evento.infoFech.evtServPr.valor = 'S' if self.reinf_competencia_id.evt_serv_pr else 'N'
        R2099.evento.infoFech.evtAssDespRec.valor = 'S' if self.reinf_competencia_id.evt_ass_desp_rec else 'N'
        R2099.evento.infoFech.evtAssDespRep.valor = 'S' if self.reinf_competencia_id.evt_ass_desp_rep else 'N'
        R2099.evento.infoFech.evtComProd.valor = 'S' if self.reinf_competencia_id.evt_com_prod else 'N'
        R2099.evento.infoFech.evtCPRB.valor = 'S' if self.reinf_competencia_id.evt_cprb else 'N'
        R2099.evento.infoFech.evtPgtos.valor = 'S' if self.reinf_competencia_id.evt_pgtos else 'N'
        if self.reinf_competencia_id.comp_sem_movto_id:
            # Calcula o Período Inicial sem Movimento (se necessário)
            comp_sem_movto = \
                self.reinf_competencia_id.comp_sem_movto_id.code[3:7] + '-' + \
                self.reinf_competencia_id.comp_sem_movto_id.code[0:2]
            R2099.evento.infoFech.compSemMovto.valor = comp_sem_movto

        return R2099

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
