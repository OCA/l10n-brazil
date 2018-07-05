# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from .sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialLotacao(models.Model, SpedRegistroIntermediario):
    _name = 'sped.esocial.lotacao'
    _description = 'Tabela de Lotações Tributárias do e-Social'
    _rec_name = 'nome'
    _order = "nome"

    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
        required=True,
    )
    lotacao_id = fields.Many2one(
        string='Lotação',
        comodel_name='res.company',
        required=True,
    )

    # S-1020 (Necessidade e Execução)
    sped_inclusao = fields.Many2one(
        string='Inclusão',
        comodel_name='sped.registro',
    )
    sped_alteracao = fields.Many2many(
        string='Alterações',
        comodel_name='sped.registro',
    )
    sped_exclusao = fields.Many2one(
        string='Exclusão',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
    )
    precisa_incluir = fields.Boolean(
        string='Precisa incluir dados?',
        compute='compute_precisa_enviar',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        compute='compute_precisa_enviar',
    )
    precisa_excluir = fields.Boolean(
        string='Precisa excluir dados?',
        compute='compute_precisa_enviar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('lotacao_id')
    def _compute_nome(self):
        for lotacao in self:
            nome = ""
            if lotacao.lotacao_id:
                nome += lotacao.lotacao_id.name
            lotacao.nome = nome

    @api.depends('sped_inclusao', 'sped_exclusao')
    def compute_situacao_esocial(self):
        for lotacao in self:
            situacao_esocial = '0'  # Inativa

            # Se a empresa possui um registro de inclusão confirmado e
            # não precisa atualizar nem excluir então ela está Ativa
            if lotacao.sped_inclusao and \
                    lotacao.sped_inclusao.situacao == '4':
                if not lotacao.precisa_atualizar and not \
                        lotacao.precisa_excluir:
                    situacao_esocial = '1'
                else:
                    situacao_esocial = '2'

                # Se já possui um registro de exclusão confirmado, então
                # é situação é Finalizada
                if lotacao.sped_exclusao and \
                        lotacao.sped_exclusao.situacao == '4':
                    situacao_esocial = '9'

            # Se a empresa possui algum registro que esteja em fase de
            # transmissão então a situação é Aguardando Transmissão
            if lotacao.sped_inclusao and \
                    lotacao.sped_inclusao.situacao != '4':
                situacao_esocial = '3'
            if lotacao.sped_exclusao and \
                    lotacao.sped_exclusao.situacao != '4':
                situacao_esocial = '3'
            for alteracao in lotacao.sped_alteracao:
                if alteracao.situacao != '4':
                    situacao_esocial = '3'

            # Popula na tabela
            lotacao.situacao_esocial = situacao_esocial

    @api.depends('sped_inclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for lotacao in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            precisa_atualizar = False
            precisa_excluir = False

            # Se a empresa matriz tem um período inicial definido e não
            # tem um registro S1000 de inclusão # confirmado,
            # então precisa incluir
            if lotacao.company_id.esocial_periodo_inicial_id:
                if not lotacao.sped_inclusao or \
                        lotacao.sped_inclusao.situacao != '4':
                    precisa_incluir = True

            # Se a empresa já tem um registro de inclusão confirmado mas a
            # data da última atualização é menor que a o write_date da empresa,
            # então precisa atualizar
            if lotacao.sped_inclusao and \
                    lotacao.sped_inclusao.situacao == '4':
                if lotacao.ultima_atualizacao < \
                        lotacao.company_id.write_date:
                    precisa_atualizar = True

            # Se a empresa já tem um registro de inclusão confirmado, tem um
            # período final definido e não tem um
            # registro de exclusão confirmado, então precisa excluir
            if lotacao.sped_inclusao and \
                    lotacao.sped_inclusao.situacao == '4':
                if lotacao.company_id.esocial_periodo_final_id:
                    if not lotacao.sped_exclusao or \
                            lotacao.sped_exclusao != '4':
                        precisa_excluir = True

            # Popula os campos na tabela
            lotacao.precisa_incluir = precisa_incluir
            lotacao.precisa_atualizar = precisa_atualizar
            lotacao.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for lotacao in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if lotacao.sped_inclusao and \
                    lotacao.sped_inclusao.situacao == '4':
                ultima_atualizacao = lotacao.sped_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de
            # origem da última alteração
            for alteracao in lotacao.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Se tiver exclusão, pega a data/hora de origem da exclusão
            if lotacao.sped_exclusao and \
                    lotacao.sped_exclusao.situacao == '4':
                ultima_atualizacao = lotacao.sped_exclusao.data_hora_origem

            # Popula o campo na tabela
            lotacao.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def popula_xml(self):
        # Cria o registro
        S1020 = pysped.esocial.leiaute.S1020_2()

        # Popula ideEvento
        S1020.tpInsc = '1'
        S1020.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S1020.evento.ideEvento.tpAmb.valor = int(self.ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S1020.evento.ideEvento.procEmi.valor = '1'
        S1020.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1020.evento.ideEmpregador.tpInsc.valor = '1'
        S1020.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula infoLotacao (Informações do Lotação Tributária)
        # Inclusão TODO lidar com alteração e exclusão
        S1020.evento.infoLotacao.operacao = 'I'
        S1020.evento.infoLotacao.ideLotacao.codLotacao.valor = \
            self.origem.lotacao_id.cod_lotacao
        S1020.evento.infoLotacao.ideLotacao.iniValid.valor = \
            self.origem.esocial_id.periodo_id.code[3:7] + '-' + \
            self.origem.esocial_id.periodo_id.code[0:2]

        # Popula dadosLotacao
        S1020.evento.infoLotacao.dadosLotacao.tpLotacao.valor = \
            self.origem.lotacao_id.tp_lotacao_id.codigo
        if self.origem.lotacao_id.tp_insc_id:
            S1020.evento.infoLotacao.dadosLotacao.tpInsc.valor = \
                self.origem.lotacao_id.tp_insc_id.codigo
        if self.origem.lotacao_id.nr_insc:
            S1020.evento.infoLotacao.dadosLotacao.nrInsc.valor = \
                self.origem.lotacao_id.nr_insc

        # Popula fpasLotacao
        S1020.evento.infoLotacao.dadosLotacao.fpasLotacao.fpas.valor = \
            self.origem.lotacao_id.fpas_id.codigo
        S1020.evento.infoLotacao.dadosLotacao.fpasLotacao.codTercs.valor = \
            self.origem.lotacao_id.cod_tercs
        # S1020.evento.infoLotacao.dadosLotacao.fpasLotacao.codTercs.valor =
        # self.origem.lotacao_id.cod_tercs_id.codigo

        return S1020

    @api.multi
    def retorno_sucesso(self):
        self.ensure_one()
