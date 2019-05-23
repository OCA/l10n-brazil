# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

import pysped
from openerp import api, models, fields
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialCondicaoAmbienteTrabalho(models.Model, SpedRegistroIntermediario):
    _name = "sped.hr.treinamentos.capacitacoes"

    name = fields.Char(
        related='hr_treinamento_capacitacao_id.name'
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
        required=True,
    )
    hr_treinamento_capacitacao_id = fields.Many2one(
        string="Treinamentos e Capacitações",
        comodel_name="hr.treinamentos.capacitacoes",
        required=True,
    )
    sped_inclusao = fields.Many2many(
        string='Inclusão',
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
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    def compute_situacao_esocial(self):
        for ambiente in self:
            if ambiente.sped_inclusao:
                ambiente.situacao_esocial = ambiente.sped_inclusao[0].situacao
            else:
                ambiente.situacao_esocial = '0'

    @api.depends('sped_inclusao.situacao')
    def compute_ultima_atualizacao(self):
        # Roda todos os registros da lista
        for ambiente in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Popula o campo na tabela
            ambiente.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def gerar_registro(self, tipo_operacao='I'):
        values = {
            'tipo': 'esocial',
            'registro': 'S-2245',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'infoExpRisco',
            'origem': (
                    'hr.treinamentos.capacitacoes,%s' %
                    self.hr_treinamento_capacitacao_id.id),
            'origem_intermediario': (
                    'sped.hr.treinamentos.capacitacoes,%s' % self.id),
        }

        sped_inclusao = self.env['sped.registro'].create(values)
        self.sped_inclusao = [(4, sped_inclusao.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # S-1060
        S2245 = pysped.esocial.leiaute.S2245_2()

        S2245.tpInsc = '1'
        S2245.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        # Popula ideEvento
        indRetif = '1'
        if operacao == 'R':
            indRetif = '2'
            registro_para_retificar = self.sped_registro
            tem_retificacao = True
            while tem_retificacao:
                if registro_para_retificar.retificacao_ids and \
                        registro_para_retificar.retificacao_ids[
                            0].situacao not in ['1', '3']:
                    registro_para_retificar = \
                        registro_para_retificar.retificacao_ids[0]
                else:
                    tem_retificacao = False
            S2245.evento.ideEvento.nrRecibo.valor = \
                registro_para_retificar.recibo
        S2245.evento.ideEvento.indRetif.valor = indRetif
        S2245.evento.ideEvento.tpAmb.valor = int(ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S2245.evento.ideEvento.procEmi.valor = '1'
        S2245.evento.ideEvento.verProc.valor = 'SAB - v8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2245.evento.ideEmpregador.tpInsc.valor = '1'
        S2245.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        S2245.evento.ideVinculo.cpfTrab.valor = limpa_formatacao(
            self.hr_treinamento_capacitacao_id.contract_id.employee_id.cpf)
        S2245.evento.ideVinculo.nisTrab.valor = limpa_formatacao(
            self.hr_treinamento_capacitacao_id.contract_id.employee_id.pis_pasep)
        if self.hr_treinamento_capacitacao_id.contract_id.sped_s2200_id:
            S2245.evento.ideVinculo.matricula.valor = \
                self.hr_treinamento_capacitacao_id.contract_id.matricula
        if self.hr_treinamento_capacitacao_id.contract_id.sped_s2300_id:
            S2245.evento.ideVinculo.codCateg.valor = \
                self.hr_treinamento_capacitacao_id.contract_id.sped.categoria_trabalhador

        S2245.evento.treiCap.codTreiCap.valor = \
            self.hr_treinamento_capacitacao_id.cod_treinamento_cap_id.codigo
        if self.hr_treinamento_capacitacao_id.obs:
            S2245.evento.treiCap.obsTreiCap.valor = \
                self.hr_treinamento_capacitacao_id.obs

        if self.hr_treinamento_capacitacao_id.cod_treinamento_cap_id.codigo not in [u'1006', u'1207']:
            informacoes_complementares = \
                pysped.esocial.leiaute.S2245_InfoComplem_2()

            informacoes_complementares.dtTreiCap.valor = \
                self.hr_treinamento_capacitacao_id.data_treinamento
            informacoes_complementares.durTreiCap.valor = \
                self.hr_treinamento_capacitacao_id.duracao
            informacoes_complementares.modTreiCap.valor = \
                self.hr_treinamento_capacitacao_id.modalidade
            informacoes_complementares.tpTreiCap.valor = \
                self.hr_treinamento_capacitacao_id.tipo
            informacoes_complementares.indTreinAnt.valor = \
                self.hr_treinamento_capacitacao_id.treinamento_antes_admissao

            for dados_professor in self.hr_treinamento_capacitacao_id.professor_ids:
                professor_tag = pysped.esocial.leiaute.S2245_IdeProfResp_2()

                if dados_professor.cpf:
                    professor_tag.cpfProf.valor = dados_professor.cpf
                professor_tag.nmProf.valor = dados_professor.nome
                professor_tag.tpProf.valor = dados_professor.tipo_vinculo
                professor_tag.formProf.valor = dados_professor.formacao
                professor_tag.codCBO.valor = dados_professor.cod_CBO
                professor_tag.nacProf.valor = dados_professor.nacionalidade

                informacoes_complementares.ideProfResp.append(professor_tag)

            S2245.evento.treiCap.infoComplem.append(informacoes_complementares)

        return S2245, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        self.hr_treinamento_capacitacao_id.precisa_atualizar = False

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
