# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

import pysped
from openerp import api, models, fields
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialAmbienteTrabalho(models.Model, SpedRegistroIntermediario):
    _name = "sped.hr.ambiente.trabalho"

    name = fields.Char(
        related='hr_ambiente_trabalho_id.cod_ambiente'
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
        required=True,
    )
    hr_ambiente_trabalho_id = fields.Many2one(
        string="Ambiente de Trabalho",
        comodel_name="hr.ambiente.trabalho",
        required=True,
    )
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
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Retificado'),
            ('7', 'Excluído'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
        store=True,
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao')
    def compute_situacao_esocial(self):
        for ambiente in self:
            if not ambiente.sped_inclusao or ambiente.sped_inclusao.situacao not in ('4', '6'):
                ambiente.situacao_esocial = '0'
                continue

            if ambiente.sped_exclusao:
                ambiente.situacao_esocial = ambiente.sped_exclusao.situacao

            if ambiente.sped_alteracao and not ambiente.sped_exclusao:
                ambiente.situacao_esocial = ambiente.sped_alteracao[0].situacao

            if ambiente.sped_inclusao and not ambiente.sped_alteracao and not ambiente.sped_exclusao:
                ambiente.situacao_esocial = ambiente.sped_inclusao.situacao

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for turno in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if turno.sped_inclusao and \
                    turno.sped_inclusao.situacao == '4':
                ultima_atualizacao = turno.sped_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de
            # origem da última alteração
            for alteracao in turno.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Se tiver exclusão, pega a data/hora de origem da exclusão
            if turno.sped_exclusao and \
                    turno.sped_exclusao.situacao == '4':
                ultima_atualizacao = turno.sped_exclusao.data_hora_origem

            # Popula o campo na tabela
            turno.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def gerar_registro(self, tipo_operacao='I'):
        values = {
            'tipo': 'esocial',
            'registro': 'S-1060',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtTabAmbiente',
            'origem': (
                    'hr.ambiente.trabalho,%s' %
                    self.hr_ambiente_trabalho_id.id),
            'origem_intermediario': (
                    'sped.hr.ambiente.trabalho,%s' % self.id),
        }
        if tipo_operacao == 'I':
            values['operacao'] = 'I'
            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_inclusao = sped_inclusao
        elif tipo_operacao == 'A':
            # Verifica se já tem um registro de atualização em aberto
            reg = False
            for registro in self.sped_alteracao:
                if registro.situacao in ['2', '3']:
                    reg = registro
            if not reg:
                values['operacao'] = 'A'
                sped_alteracao = self.env['sped.registro'].create(values)
                self.sped_alteracao = sped_alteracao
        elif tipo_operacao == 'E':
            values['operacao'] = 'E'
            sped_exclusao = self.env['sped.registro'].create(values)
            self.sped_exclusao = sped_exclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # S-1060
        S1060 = pysped.esocial.leiaute.S1060_2()

        S1060.tpInsc = '1'
        S1060.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        # Popula ideEvento
        S1060.evento.ideEvento.tpAmb.valor = int(ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S1060.evento.ideEvento.procEmi.valor = '1'
        S1060.evento.ideEvento.verProc.valor = 'SAB - v8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1060.evento.ideEmpregador.tpInsc.valor = '1'
        S1060.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        if operacao == 'I':
            inclusao = pysped.esocial.leiaute.S1060_Inclusao()

            # Popula ideAmbiente
            inclusao.ideAmbiente.codAmb.valor = self.hr_ambiente_trabalho_id.cod_ambiente
            inclusao.ideAmbiente.iniValid.valor = '{}-{}'.format(self.hr_ambiente_trabalho_id.data_inicio.code[3:7], self.hr_ambiente_trabalho_id.data_inicio.code[0:2])
            if self.hr_ambiente_trabalho_id.data_fim:
                inclusao.ideAmbiente.fimValid.valor = '{}-{}'.format(self.hr_ambiente_trabalho_id.data_fim.code[3:7], self.hr_ambiente_trabalho_id.data_fim.code[0:2])

            # Popula dadosAmbiente
            inclusao.dadosAmbiente.nmAmb.valor = self.hr_ambiente_trabalho_id.nome_ambiente
            inclusao.dadosAmbiente.dscAmb.valor = self.hr_ambiente_trabalho_id.desc_ambiente
            inclusao.dadosAmbiente.localAmb.valor = self.hr_ambiente_trabalho_id.local_ambiente
            if self.hr_ambiente_trabalho_id.local_ambiente in [1, 3]:
                inclusao.dadosAmbiente.tpInsc.valor = self.hr_ambiente_trabalho_id.tipo_inscricao.codigo
                inclusao.dadosAmbiente.nrInsc.valor = self.hr_ambiente_trabalho_id.num_inscricao
            else:
                inclusao.dadosAmbiente.codLotacao.valor = self.hr_ambiente_trabalho_id.cod_lotacao

            S1060.evento.infoAmbiente.inclusao.append(inclusao)
        elif operacao == 'A':
            alteracao = pysped.esocial.leiaute.S1060_Alteracao()

            # Popula ideAmbiente
            alteracao.ideAmbiente.codAmb.valor = self.hr_ambiente_trabalho_id.cod_ambiente
            alteracao.ideAmbiente.iniValid.valor = '{}-{}'.format(
                self.hr_ambiente_trabalho_id.data_inicio.code[3:7],
                self.hr_ambiente_trabalho_id.data_inicio.code[0:2])
            if self.hr_ambiente_trabalho_id.data_fim:
                alteracao.ideAmbiente.fimValid.valor = '{}-{}'.format(
                    self.hr_ambiente_trabalho_id.data_fim.code[3:7],
                    self.hr_ambiente_trabalho_id.data_fim.code[0:2])

            # Popula dadosAmbiente
            alteracao.dadosAmbiente.nmAmb.valor = self.hr_ambiente_trabalho_id.nome_ambiente
            alteracao.dadosAmbiente.dscAmb.valor = self.hr_ambiente_trabalho_id.desc_ambiente
            alteracao.dadosAmbiente.localAmb.valor = self.hr_ambiente_trabalho_id.local_ambiente
            if self.hr_ambiente_trabalho_id.local_ambiente in [1, 3]:
                alteracao.dadosAmbiente.tpInsc.valor = self.hr_ambiente_trabalho_id.tipo_inscricao.codigo
                alteracao.dadosAmbiente.nrInsc.valor = self.hr_ambiente_trabalho_id.num_inscricao
            else:
                alteracao.dadosAmbiente.codLotacao.valor = self.hr_ambiente_trabalho_id.cod_lotacao

            if self.hr_ambiente_trabalho_id.nova_data_inicio:
                nova_validade = pysped.esocial.leiaute.s1060_NovaValidade_2()
                nova_validade.iniValid.valor = '{}-{}'.format(
                    self.hr_ambiente_trabalho_id.nova_data_inicio.code[3:7],
                    self.hr_ambiente_trabalho_id.nova_data_inicio.code[0:2])
                if self.hr_ambiente_trabalho_id.nova_data_fim:
                    nova_validade.fimValid.valor = '{}-{}'.format(
                       self.hr_ambiente_trabalho_id.nova_data_fim.code[3:7],
                       self.hr_ambiente_trabalho_id.nova_data_fim.code[0:2])

                alteracao.novaValidade.append(nova_validade)

            S1060.evento.infoAmbiente.alteracao.append(alteracao)
        elif operacao == 'E':
            exclusao = pysped.esocial.leiaute.S1060_Exclusao()

            # Popula ideAmbiente
            exclusao.ideAmbiente.codAmb.valor = self.hr_ambiente_trabalho_id.cod_ambiente
            exclusao.ideAmbiente.iniValid.valor = '{}-{}'.format(
                self.hr_ambiente_trabalho_id.data_inicio.code[3:7],
                self.hr_ambiente_trabalho_id.data_inicio.code[0:2])
            if self.hr_ambiente_trabalho_id.data_fim:
                exclusao.ideAmbiente.fimValid.valor = '{}-{}'.format(
                    self.hr_ambiente_trabalho_id.data_fim.code[3:7],
                    self.hr_ambiente_trabalho_id.data_fim.code[0:2])

            S1060.evento.infoAmbiente.exclusao.append(exclusao)

        return S1060, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        self.hr_ambiente_trabalho_id.precisa_atualizar = False

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
