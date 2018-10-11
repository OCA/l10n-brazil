# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialRubrica(models.Model, SpedRegistroIntermediario):
    _name = 'sped.esocial.rubrica'
    _description = 'Tabela de Rubricas e-Social'
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
    rubrica_id = fields.Many2one(
        string='Rubricas',
        comodel_name='hr.salary.rule',
        required=True,
    )

    # S-1010 (Necessidade e Execução)
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
        inverse='inverse_situacao_esocial',
        store=True,
    )
    precisa_incluir = fields.Boolean(
        string='Precisa incluir dados?',
        compute='compute_precisa_enviar',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
    )
    precisa_excluir = fields.Boolean(
        string='Precisa excluir dados?',
        compute='compute_precisa_enviar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('rubrica_id')
    def _compute_nome(self):
        for rubrica in self:
            nome = "Rubrica"
            if rubrica.rubrica_id:
                nome += ' ('
                nome += rubrica.rubrica_id.display_name or ''
                nome += ')'

            rubrica.nome = nome

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao',
                 'sped_exclusao.situacao', 'precisa_atualizar')
    def inverse_situacao_esocial(self):
        """
        Função apenas para liberar edição do campo situacao_esocial
        :return:
        """
        for rubrica in self:
            pass

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao', 'precisa_atualizar')
    def compute_situacao_esocial(self):
        for rubrica in self:
            situacao_esocial = '0'  # Inativa

            # Se a empresa possui um registro de inclusão confirmado e
            # não precisa atualizar nem excluir então ela está Ativa
            if rubrica.sped_inclusao and \
                    rubrica.sped_inclusao.situacao == '4':
                if not rubrica.precisa_atualizar and not \
                        rubrica.precisa_excluir:
                    situacao_esocial = '1'
                else:
                    situacao_esocial = '2'

                # Se já possui um registro de exclusão confirmado, então
                # é situação é Finalizada
                if rubrica.sped_exclusao and \
                        rubrica.sped_exclusao.situacao == '4':
                    situacao_esocial = '9'

            # Se a empresa possui algum registro que esteja em fase de
            # transmissão então a situação é Aguardando Transmissão
            if rubrica.sped_inclusao and \
                    rubrica.sped_inclusao.situacao != '4':
                situacao_esocial = '3'
                registro = rubrica.sped_inclusao
            if rubrica.sped_exclusao and \
                    rubrica.sped_exclusao.situacao != '4':
                situacao_esocial = '3'
                registro = rubrica.sped_exclusao
            for alteracao in rubrica.sped_alteracao:
                if alteracao.situacao != '4':
                    situacao_esocial = '3'
                    registro = alteracao

            # Se a situação == '3', verifica se já foi transmitida ou não (se já foi transmitida
            # então a situacao_esocial deve ser '4'
            if situacao_esocial == '3' and registro.situacao == '2':
                situacao_esocial = '4'

            # Verifica se algum registro está com erro de transmissão
            if rubrica.sped_inclusao and rubrica.sped_inclusao.situacao == '3':
                situacao_esocial = '5'
            if rubrica.sped_exclusao and rubrica.sped_exclusao.situacao == '3':
                situacao_esocial = '5'
            for alteracao in rubrica.sped_alteracao:
                if alteracao.situacao == '3':
                    situacao_esocial = '5'

            # Popula na tabela
            rubrica.situacao_esocial = situacao_esocial

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for rubrica in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            precisa_excluir = False

            # Se a rubrica tem um período inicial definido e não
            # tem um registro S1010 de inclusão # confirmado,
            # então precisa incluir
            if not rubrica.sped_inclusao:
                # or \
                #     rubrica.sped_inclusao.situacao != '4':
                precisa_incluir = True

            # Se a empresa já tem um registro de inclusão confirmado, tem um
            # período final definido e não tem um
            # registro de exclusão confirmado, então precisa excluir
            if rubrica.sped_inclusao and \
                    rubrica.sped_inclusao.situacao == '4':
                if rubrica.company_id.esocial_periodo_final_id:
                    if not rubrica.sped_exclusao or \
                            rubrica.sped_exclusao != '4':
                        precisa_excluir = True

            # Popula os campos na tabela
            rubrica.precisa_incluir = precisa_incluir
            rubrica.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for rubrica in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if rubrica.sped_inclusao and \
                    rubrica.sped_inclusao.situacao == '4':
                ultima_atualizacao = rubrica.sped_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de
            # origem da última alteração
            for alteracao in rubrica.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Se tiver exclusão, pega a data/hora de origem da exclusão
            if rubrica.sped_exclusao and \
                    rubrica.sped_exclusao.situacao == '4':
                ultima_atualizacao = rubrica.sped_exclusao.data_hora_origem

            # Popula o campo na tabela
            rubrica.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def gerar_registro(self):
        if self.precisa_incluir or self.precisa_atualizar or \
                self.precisa_excluir:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1010',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'evento': 'evtTabRubrica',
                'origem': ('hr.salary.rule,%s' % self.rubrica_id.id),
                'origem_intermediario': (
                        'sped.esocial.rubrica,%s' % self.id),
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
        S1010 = pysped.esocial.leiaute.S1010_2()

        # Popula ideEvento
        S1010.tpInsc = '1'
        S1010.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S1010.evento.ideEvento.tpAmb.valor = int(ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S1010.evento.ideEvento.procEmi.valor = '1'
        S1010.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1010.evento.ideEmpregador.tpInsc.valor = '1'
        S1010.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula infoRubrica (Informações da Rubrica)
        S1010.evento.infoRubrica.operacao = operacao
        S1010.evento.infoRubrica.ideRubrica.codRubr.valor = \
            self.rubrica_id.codigo
        S1010.evento.infoRubrica.ideRubrica.ideTabRubr.valor = \
            self.rubrica_id.identificador

        # Início da Validade neste evento
        S1010.evento.infoRubrica.ideRubrica.iniValid.valor = \
            self.rubrica_id.ini_valid.code[3:7] + '-' + \
            self.rubrica_id.ini_valid.code[0:2]

        # Inclusão não precisa adicionar mais nada aqui

        # Alteração adiciona a tag de novaValidade
        if operacao == 'A':

            if not self.rubrica_id.alt_valid:
                validacao += "O período de Alteração não está definido na Rubrica !\n"
            else:
                # Alteração da Validade neste evento
                S1010.evento.infoRubrica.novaValidade.iniValid.valor = \
                    self.rubrica_id.alt_valid.code[3:7] + '-' + \
                    self.rubrica_id.alt_valid.code[0:2]

        # Exclusão popula a tag fimValid
        if operacao == 'E':

            S1010.evento.infoRubrica.ideRubrica.fimValid.valor = \
                self.rubrica_id.fim_valid.code[3:7] + '-' + \
                self.rubrica_id.fim_valid.code[0:2]

        # Preencher dadosRubrica
        S1010.evento.infoRubrica.dadosRubrica.dscRubr.valor = \
            self.rubrica_id.name
        S1010.evento.infoRubrica.dadosRubrica.natRubr.valor = \
            self.rubrica_id.nat_rubr.codigo
        S1010.evento.infoRubrica.dadosRubrica.tpRubr.valor = \
            self.rubrica_id.tp_rubr
        S1010.evento.infoRubrica.dadosRubrica.codIncFGTS.valor = \
            self.rubrica_id.cod_inc_fgts
        S1010.evento.infoRubrica.dadosRubrica.codIncSIND.valor = \
            self.rubrica_id.cod_inc_sind

        # Preencher codIncCP
        if self.rubrica_id.cod_inc_cp == '0':
            cod_inc_cp = self.rubrica_id.cod_inc_cp_0
        elif self.rubrica_id.cod_inc_cp == '1':
            cod_inc_cp = self.rubrica_id.cod_inc_cp_1
        elif self.rubrica_id.cod_inc_cp == '3':
            cod_inc_cp = self.rubrica_id.cod_inc_cp_3
        elif self.rubrica_id.cod_inc_cp == '5':
            cod_inc_cp = self.rubrica_id.cod_inc_cp_5
        elif self.rubrica_id.cod_inc_cp == '9':
            cod_inc_cp = self.rubrica_id.cod_inc_cp_9
        S1010.evento.infoRubrica.dadosRubrica.codIncCP.valor = cod_inc_cp

        # Preencher codIncIRRF
        if self.rubrica_id.cod_inc_irrf == '0':
            cod_inc_irrf = self.rubrica_id.cod_inc_irrf_0
        elif self.rubrica_id.cod_inc_irrf == '1':
            cod_inc_irrf = self.rubrica_id.cod_inc_irrf_1
        elif self.rubrica_id.cod_inc_irrf == '3':
            cod_inc_irrf = self.rubrica_id.cod_inc_irrf_3
        elif self.rubrica_id.cod_inc_irrf == '4':
            cod_inc_irrf = self.rubrica_id.cod_inc_irrf_4
        elif self.rubrica_id.cod_inc_irrf == '7':
            cod_inc_irrf = self.rubrica_id.cod_inc_irrf_7
        elif self.rubrica_id.cod_inc_irrf == '8':
            cod_inc_irrf = self.rubrica_id.cod_inc_irrf_8
        elif self.rubrica_id.cod_inc_irrf == '9':
            cod_inc_irrf = self.rubrica_id.cod_inc_irrf_9
        S1010.evento.infoRubrica.dadosRubrica.codIncIRRF.valor = cod_inc_irrf

        # Preencher observação
        if self.rubrica_id.note:
            S1010.evento.infoRubrica.dadosRubrica.observacao.valor = \
                self.rubrica_id.note

        return S1010, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
        self.precisa_atualizar = False
        self.situacao_esocial = '1'

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


# class HrSalaryRule(models.Model):
#     _inherit = "hr.salary.rule"
#
#     sped_esocial_rubrica_ids = fields.One2many(
#         comodel_name='sped.esocial.rubrica',
#         inverse_name='rubrica_id',
#     )
