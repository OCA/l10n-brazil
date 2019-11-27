# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialLotacao(models.Model, SpedRegistroIntermediario):
    _name = 'sped.esocial.lotacao'
    _description = 'Tabela de Lotações Tributárias do e-Social'
    _rec_name = "nome"
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
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
        store=True,
    )
    precisa_incluir = fields.Boolean(
        string='Precisa incluir dados?',
        compute='compute_precisa_enviar',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        related='lotacao_id.precisa_atualizar_lotacao',
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
            nome = "Lotação Tributária "
            if lotacao.lotacao_id:
                nome += ' ('
                nome += lotacao.lotacao_id.name or ''
            nome += ')'
            lotacao.nome = nome

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao', 'lotacao_id.precisa_atualizar_lotacao')
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
                registro = lotacao.sped_inclusao
            if lotacao.sped_exclusao and \
                    lotacao.sped_exclusao.situacao != '4':
                situacao_esocial = '3'
                registro = lotacao.sped_exclusao
            for alteracao in lotacao.sped_alteracao:
                if alteracao.situacao != '4':
                    situacao_esocial = '3'
                    registro = alteracao

            # Se a situação == '3', verifica se já foi transmitida ou não (se já foi transmitida
            # então a situacao_esocial deve ser '4'
            if situacao_esocial == '3' and registro.situacao == '2':
                situacao_esocial = '4'

            # Verifica se algum registro está com erro de transmissão
            if lotacao.sped_inclusao and lotacao.sped_inclusao.situacao == '3':
                situacao_esocial = '5'
            if lotacao.sped_exclusao and lotacao.sped_exclusao.situacao == '3':
                situacao_esocial = '5'
            for alteracao in lotacao.sped_alteracao:
                if alteracao.situacao == '3':
                    situacao_esocial = '5'

            # Popula na tabela
            lotacao.situacao_esocial = situacao_esocial

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for lotacao in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            precisa_excluir = False

            # Se a empresa matriz tem um período inicial definido e não
            # tem um registro S1000 de inclusão # confirmado,
            # então precisa incluir
            if not lotacao.sped_inclusao or \
                        lotacao.sped_inclusao.situacao != '4':
                precisa_incluir = True

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
            lotacao.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao')
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
    def gerar_registro(self):
        values = {
            'tipo': 'esocial',
            'registro': 'S-1020',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtTabLotacao',
            'origem': ('res.company,%s' % self.lotacao_id.id),
            'origem_intermediario': (
                    'sped.esocial.lotacao,%s' % self.id),
        }
        if self.precisa_incluir and not self.sped_inclusao:
            values['operacao'] = 'I'
            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_inclusao = sped_inclusao
        elif self.precisa_atualizar:
            # Verifica se já tem um registro de atualização em aberto
            reg = False
            for registro in self.sped_alteracao:
                if registro.situacao in ['2', '3']:
                    reg = registro
            if not reg:
                values['operacao'] = 'A'
                sped_alteracao = self.env['sped.registro'].create(values)
                self.sped_inclusao = sped_alteracao
        elif self.precisa_excluir and not self.sped_exclusao:
            values['operacao'] = 'E'
            sped_exclusao = self.env['sped.registro'].create(values)
            self.sped_exclusao = sped_exclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # Cria o registro
        S1020 = pysped.esocial.leiaute.S1020_2()

        # Popula ideEvento
        S1020.tpInsc = '1'
        S1020.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S1020.evento.ideEvento.tpAmb.valor = int(ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S1020.evento.ideEvento.procEmi.valor = '1'
        S1020.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1020.evento.ideEmpregador.tpInsc.valor = '1'
        S1020.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula infoLotacao (Informações do Lotação Tributária)
        S1020.evento.infoLotacao.operacao = operacao
        S1020.evento.infoLotacao.ideLotacao.codLotacao.valor = \
            self.lotacao_id.cod_lotacao
        S1020.evento.infoLotacao.ideLotacao.iniValid.valor = \
            self.lotacao_id.lotacao_periodo_inicial_id.code[3:7] + '-' + \
            self.lotacao_id.lotacao_periodo_inicial_id.code[0:2]

        # Inclusão, não precisa fazer mais nada

        # Alteração, incluir a tag novaValidade
        if operacao == 'A':

            if not self.lotacao_id.lotacao_periodo_atualizacao_id:
                validacao += "O período de Atualização da Lotação Tributária não está definido na Empresa !\n"
            else:
                S1020.evento.infoLotacao.novaValidade.iniValid.valor = \
                    self.lotacao_id.lotacao_periodo_atualizacao_id.code[3:7] + '-' + \
                    self.lotacao_id.lotacao_periodo_atualizacao_id.code[0:2]

        # Exclusão popula a tag fimValid
        if operacao == 'E':

            S1020.evento.infoLotacao.ideLotacao.fimValid.valor = \
                self.lotacao_id.lotacao_periodo_final_id.code[3:7] + '-' + \
                self.lotacao_id.lotacao_periodo_final_id.code[0:2]

        # Popula dadosLotacao
        S1020.evento.infoLotacao.dadosLotacao.tpLotacao.valor = \
            self.lotacao_id.tp_lotacao_id.codigo
        # if self.lotacao_id.tp_insc_id:
        #     S1020.evento.infoLotacao.dadosLotacao.tpInsc.valor = \
        #         self.lotacao_id.tp_insc_id.codigo
        # if self.lotacao_id.nr_insc:
        #     S1020.evento.infoLotacao.dadosLotacao.nrInsc.valor = \
        #         self.lotacao_id.nr_insc

        # Popula fpasLotacao
        S1020.evento.infoLotacao.dadosLotacao.fpasLotacao.fpas.valor = \
            self.lotacao_id.fpas_id.codigo
        S1020.evento.infoLotacao.dadosLotacao.fpasLotacao.codTercs.valor = \
            self.lotacao_id.cod_tercs
        # S1020.evento.infoLotacao.dadosLotacao.fpasLotacao.codTercs.valor =
        # self.origem.lotacao_id.cod_tercs_id.codigo

        return S1020, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
        self.lotacao_id.precisa_atualizar_lotacao = False

    @api.multi
    def transmitir(self):
        self.ensure_one()

        if self.situacao_esocial in ['2', '3', '5']:
            # Identifica qual registro precisa transmitir
            registro = False
            if self.sped_inclusao.situacao in ['1', '3']:
                registro = self.sped_inclusao
            else:
                for r in self.sped_alteracao:
                    if r.situacao in ['1', '3']:
                        registro = r

            if not registro:
                if self.sped_exclusao.situacao in ['1', '3']:
                    registro = self.sped_exclusao

            # Com o registro identificado, é só rodar o método transmitir_lote() do registro
            if registro:
                registro.transmitir_lote()

    @api.multi
    def consultar(self):
        self.ensure_one()

        if self.situacao_esocial in ['4']:
            # Identifica qual registro precisa consultar
            registro = False
            if self.sped_inclusao.situacao == '2':
                registro = self.sped_inclusao
            else:
                for r in self.sped_alteracao:
                    if r.situacao == '2':
                        registro = r

            if not registro:
                if self.sped_exclusao == '2':
                    registro = self.sped_exclusao

            # Com o registro identificado, é só rodar o método consulta_lote() do registro
            if registro:
                registro.consulta_lote()
