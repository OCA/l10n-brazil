# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialCargo(models.Model, SpedRegistroIntermediario):
    _name = 'sped.esocial.cargo'
    _description = 'Tabela de Cargos e-Social'
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
    cargo_id = fields.Many2one(
        string='Cargos',
        comodel_name='hr.job',
        required=True,
    )

    # S-1030 (Necessidade e Execução)
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
            ('0', 'Inativo(a)'),
            ('1', 'Ativo(a)'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado(a)'),
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
        related='cargo_id.precisa_atualizar',
    )
    precisa_excluir = fields.Boolean(
        string='Precisa excluir dados?',
        compute='compute_precisa_enviar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('cargo_id')
    def _compute_nome(self):
        for cargo in self:
            nome = "Cargo"
            if cargo.cargo_id:
                nome += ' ('
                nome += cargo.cargo_id.name or ''
                nome += ')'

            cargo.nome = nome

    @api.depends('sped_inclusao', 'sped_exclusao')
    def compute_situacao_esocial(self):
        for cargo in self:
            situacao_esocial = '0'  # Inativa

            # Se a empresa possui um registro de inclusão confirmado e
            # não precisa atualizar nem excluir então ela está Ativa
            if cargo.sped_inclusao and \
                    cargo.sped_inclusao.situacao == '4':
                if not cargo.precisa_atualizar and not \
                        cargo.precisa_excluir:
                    situacao_esocial = '1'
                else:
                    situacao_esocial = '2'

                # Se já possui um registro de exclusão confirmado, então
                # é situação é Finalizada
                if cargo.sped_exclusao and \
                        cargo.sped_exclusao.situacao == '4':
                    situacao_esocial = '9'

            # Se a empresa possui algum registro que esteja em fase de
            # transmissão então a situação é Aguardando Transmissão
            if cargo.sped_inclusao and \
                    cargo.sped_inclusao.situacao != '4':
                situacao_esocial = '3'
                registro = cargo.sped_inclusao
            if cargo.sped_exclusao and \
                    cargo.sped_exclusao.situacao != '4':
                situacao_esocial = '3'
                registro = cargo.sped_exclusao
            for alteracao in cargo.sped_alteracao:
                if alteracao.situacao != '4':
                    situacao_esocial = '3'
                    registro = alteracao

            # Se a situação == '3', verifica se já foi transmitida ou não (se já foi transmitida
            # então a situacao_esocial deve ser '4'
            if situacao_esocial == '3' and registro.situacao == '2':
                situacao_esocial = '4'

            # Verifica se algum registro está com erro de transmissão
            if cargo.sped_inclusao and cargo.sped_inclusao.situacao == '3':
                situacao_esocial = '5'
            if cargo.sped_exclusao and cargo.sped_exclusao.situacao == '3':
                situacao_esocial = '5'
            for alteracao in cargo.sped_alteracao:
                if alteracao.situacao == '3':
                    situacao_esocial = '5'

            # Popula na tabela
            cargo.situacao_esocial = situacao_esocial

    @api.depends('sped_inclusao', 'sped_exclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'cargo_id.precisa_atualizar')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for cargo in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            precisa_atualizar = False
            precisa_excluir = False

            # Se a empresa matriz tem um período inicial definido e não
            # tem um registro S1000 de inclusão # confirmado,
            # então precisa incluir
            if cargo.company_id.esocial_periodo_inicial_id:
                if not cargo.sped_inclusao or \
                        cargo.sped_inclusao.situacao != '4':
                    precisa_incluir = True

            # Se a empresa já tem um registro de inclusão confirmado, tem um
            # período final definido e não tem um
            # registro de exclusão confirmado, então precisa excluir
            if cargo.sped_inclusao and \
                    cargo.sped_inclusao.situacao == '4':
                if cargo.company_id.esocial_periodo_final_id:
                    if not cargo.sped_exclusao or \
                            cargo.sped_exclusao != '4':
                        precisa_excluir = True

            # Popula os campos na tabela
            cargo.precisa_incluir = precisa_incluir
            cargo.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for cargo in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if cargo.sped_inclusao and \
                    cargo.sped_inclusao.situacao == '4':
                ultima_atualizacao = cargo.sped_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de
            # origem da última alteração
            for alteracao in cargo.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Se tiver exclusão, pega a data/hora de origem da exclusão
            if cargo.sped_exclusao and \
                    cargo.sped_exclusao.situacao == '4':
                ultima_atualizacao = cargo.sped_exclusao.data_hora_origem

            # Popula o campo na tabela
            cargo.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def gerar_registro(self):
        if self.precisa_incluir or self.precisa_atualizar or \
                self.precisa_excluir:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1030',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'evento': 'evtTabCargo',
                'origem': ('hr.job,%s' % self.cargo_id.id),
                'origem_intermediario': (
                        'sped.esocial.cargo,%s' % self.id),
            }
            if self.precisa_incluir:
                values['operacao'] = 'I'
                sped_inclusao = self.env['sped.registro'].create(values)
                self.sped_inclusao = sped_inclusao
            elif self.precisa_atualizar:
                values['operacao'] = 'A'
                sped_alteracao = self.env['sped.registro'].create(values)
                self.sped_alteracao = [(4, sped_alteracao.id)]
            elif self.precisa_excluir:
                values['operacao'] = 'E'
                sped_exclusao = self.env['sped.registro'].create(values)
                self.sped_exclusao = sped_exclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        # Cria o registro
        S1030 = pysped.esocial.leiaute.S1030_2()

        # Popula ideEvento
        S1030.tpInsc = '1'
        S1030.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S1030.evento.ideEvento.tpAmb.valor = int(ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S1030.evento.ideEvento.procEmi.valor = '1'
        S1030.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1030.evento.ideEmpregador.tpInsc.valor = '1'
        S1030.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula infoCargo (Informações da Rubrica)
        # Inclusão
        S1030.evento.infoCargo.operacao = operacao
        S1030.evento.infoCargo.ideCargo.codCargo.valor = \
            self.cargo_id.codigo

        # Início da Validade neste evento
        S1030.evento.infoCargo.ideCargo.iniValid.valor = \
            self.cargo_id.ini_valid.code[3:7] + '-' + \
            self.cargo_id.ini_valid.code[0:2]

        if operacao == 'A':
            S1030.evento.infoCargo.novaValidade.iniValid.valor = \
                self.cargo_id.alt_valid.code[3:7] + '-' + \
                self.cargo_id.alt_valid.code[0:2]

        # Preencher dadosCargo
        S1030.evento.infoCargo.dadosCargo.nmCargo.valor = \
            self.cargo_id.name
        S1030.evento.infoCargo.dadosCargo.codCBO.valor = \
            self.cargo_id.cbo_id.code

        # Preencher dados de cargoPublico (se for o caso)
        if self.cargo_id.cargo_publico:
            CargoPublico = pysped.esocial.leiaute.S1030_CargoPublico_2()
            CargoPublico.acumCargo.valor = self.cargo_id.acum_cargo
            CargoPublico.contagemEsp.valor = self.cargo_id.contagem_esp
            CargoPublico.dedicExcl.valor = self.cargo_id.dedic_excl
            CargoPublico.nrLei.valor = self.cargo_id.nr_lei
            CargoPublico.dtLei.valor = self.cargo_id.dt_lei
            CargoPublico.sitCargo.valor = self.cargo_id.sit_cargo

        return S1030

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        # Desativa o campo 'precisa_atualizar' no cargo
        self.cargo_id.precisa_atualizar = False

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
