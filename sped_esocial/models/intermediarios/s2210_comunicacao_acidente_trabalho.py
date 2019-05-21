# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

import pysped
from openerp import api, models, fields
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialComunicacaoAcidenteTrabalho(models.Model, SpedRegistroIntermediario):
    _name = "sped.hr.comunicacao.acidente.trabalho"

    name = fields.Char(
        related='hr_comunicacao_acidente_trabalho_id.name'
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
        required=True,
    )
    hr_comunicacao_acidente_trabalho_id = fields.Many2one(
        string="Comunicação de Acidente de Trabalho",
        comodel_name="hr.comunicacao.acidente.trabalho",
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
            'registro': 'S-2210',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtMonit',
            'origem': (
                    'hr.comunicacao.acidente.trabalho,%s' %
                    self.hr_comunicacao_acidente_trabalho_id.id),
            'origem_intermediario': (
                    'sped.hr.comunicacao.acidente.trabalho,%s' % self.id),
        }

        sped_inclusao = self.env['sped.registro'].create(values)
        self.sped_inclusao = [(4, sped_inclusao.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # S-1060
        S2210 = pysped.esocial.leiaute.S2210_2()

        S2210.tpInsc = '1'
        S2210.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
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
            S2210.evento.ideEvento.nrRecibo.valor = \
                registro_para_retificar.recibo
        S2210.evento.ideEvento.indRetif.valor = indRetif
        S2210.evento.ideEvento.tpAmb.valor = int(ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S2210.evento.ideEvento.procEmi.valor = '1'
        S2210.evento.ideEvento.verProc.valor = 'SAB - v8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2210.evento.ideEmpregador.tpInsc.valor = '1'
        S2210.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        S2210.evento.ideVinculo.cpfTrab.valor = limpa_formatacao(
            self.hr_comunicacao_acidente_trabalho_id.contract_id.employee_id.cpf)
        S2210.evento.ideVinculo.nisTrab.valor = limpa_formatacao(
            self.hr_comunicacao_acidente_trabalho_id.contract_id.employee_id.pis_pasep)

        S2210.evento.cat.dtAcid.valor = self.hr_comunicacao_acidente_trabalho_id.data_acidente.split(' ')[0]
        S2210.evento.cat.tpAcid.valor = self.hr_comunicacao_acidente_trabalho_id.tipo_acidente.codigo
        S2210.evento.cat.hrAcid.valor = self.hr_comunicacao_acidente_trabalho_id.data_acidente.split(' ')[1].replace(':', '')[:4]
        S2210.evento.cat.hrsTrabAntesAcid.valor = self.hr_comunicacao_acidente_trabalho_id.horas_trab_antes_acidente
        S2210.evento.cat.tpCat.valor = self.hr_comunicacao_acidente_trabalho_id.tipo_cat
        S2210.evento.cat.indCatObito.valor = self.hr_comunicacao_acidente_trabalho_id.ind_cat_obito
        if self.hr_comunicacao_acidente_trabalho_id.data_obito:
            S2210.evento.cat.dtObito.valor = self.hr_comunicacao_acidente_trabalho_id.data_obito
        S2210.evento.cat.indComunPolicia.valor = self.hr_comunicacao_acidente_trabalho_id.ind_comunicacao_policia
        S2210.evento.cat.codSitGeradora.valor = self.hr_comunicacao_acidente_trabalho_id.cod_geradora_acidente.codigo
        S2210.evento.cat.iniciatCAT.valor = self.hr_comunicacao_acidente_trabalho_id.emissao_cat
        if self.hr_comunicacao_acidente_trabalho_id.obs:
            S2210.evento.cat.obsCAT.valor = self.hr_comunicacao_acidente_trabalho_id.obs
        S2210.evento.cat.localAcidente.tpLocal.valor = self.hr_comunicacao_acidente_trabalho_id.tipo_local
        if self.hr_comunicacao_acidente_trabalho_id.desc_local:
            S2210.evento.cat.localAcidente.dscLocal.valor = self.hr_comunicacao_acidente_trabalho_id.desc_local
        if self.hr_comunicacao_acidente_trabalho_id.cod_ambiente:
            S2210.evento.cat.localAcidente.codAmb.valor = self.hr_comunicacao_acidente_trabalho_id.cod_ambiente
        S2210.evento.cat.localAcidente.tpLograd.valor = self.hr_comunicacao_acidente_trabalho_id.tipo_logradouro.codigo
        S2210.evento.cat.localAcidente.dscLograd.valor = self.hr_comunicacao_acidente_trabalho_id.desc_logradouro
        S2210.evento.cat.localAcidente.nrLograd.valor = self.hr_comunicacao_acidente_trabalho_id.num_logradouro
        if self.hr_comunicacao_acidente_trabalho_id.complemento:
            S2210.evento.cat.localAcidente.complemento.valor = self.hr_comunicacao_acidente_trabalho_id.complemento
        if self.hr_comunicacao_acidente_trabalho_id.bairro:
            S2210.evento.cat.localAcidente.bairro.valor = self.hr_comunicacao_acidente_trabalho_id.bairro
        if self.hr_comunicacao_acidente_trabalho_id.cep:
            S2210.evento.cat.localAcidente.cep.valor = self.hr_comunicacao_acidente_trabalho_id.cep
        if self.hr_comunicacao_acidente_trabalho_id.city_id:
            S2210.evento.cat.localAcidente.codMunic.valor = '{:07d}'.format(int(self.hr_comunicacao_acidente_trabalho_id.city_id.ibge_code))
        if self.hr_comunicacao_acidente_trabalho_id.uf_id:
            S2210.evento.cat.localAcidente.uf.valor = self.hr_comunicacao_acidente_trabalho_id.uf_id.code
        if self.hr_comunicacao_acidente_trabalho_id.country_id:
            S2210.evento.cat.localAcidente.pais.valor = self.hr_comunicacao_acidente_trabalho_id.country_id.bc_code
        if self.hr_comunicacao_acidente_trabalho_id.cod_postal:
            S2210.evento.cat.localAcidente.codPostal.valor = self.hr_comunicacao_acidente_trabalho_id.cod_postal

        identificacao_local = pysped.esocial.leiaute.S2210_IdeLocalAcid_2()
        identificacao_local.tpInsc.valor = self.hr_comunicacao_acidente_trabalho_id.tipo_inscricao_local.codigo
        identificacao_local.nrInsc.valor = self.hr_comunicacao_acidente_trabalho_id.num_inscricao

        S2210.evento.cat.localAcidente.ideLocalAcid.append(identificacao_local)

        for parte_atingida in self.hr_comunicacao_acidente_trabalho_id.parte_atingida_ids:
            parteAtingida = pysped.esocial.leiaute.S2210_ParteAtingida_2()

            parteAtingida.codParteAting.valor = parte_atingida.cod_parte_atingida.codigo
            parteAtingida.lateralidade.valor = parte_atingida.lateralidade

            S2210.evento.cat.parteAtingida.append(parteAtingida)

        for agente_causador in self.hr_comunicacao_acidente_trabalho_id.agente_causador_ids:
            agenteCausador = pysped.esocial.leiaute.S2210_AgenteCausador_2()

            if agente_causador.cod_agente_causador_id.codigo:
                agenteCausador.codAgntCausador.valor = agente_causador.cod_agente_causador_id.codigo
            if agente_causador.cod_agente_causador_doenca_id:
                agenteCausador.codAgntCausador.valor = agente_causador.cod_agente_causador_doenca_id.codigo

            S2210.evento.cat.agenteCausador.append(agenteCausador)

        for atestado in self.hr_comunicacao_acidente_trabalho_id.atestado_medico_id:
            atestado_tag = pysped.esocial.leiaute.S2210_Atestado_2()

            if atestado.cod_cnes:
                atestado_tag.codCNES.valor = atestado.cod_cnes
            atestado_tag.dtAtendimento.valor = atestado.data_atendimento.split(' ')[0]
            atestado_tag.hrAtendimento.valor = atestado.data_atendimento.split(' ')[1].replace(':', '')[:4]
            atestado_tag.indInternacao.valor = atestado.indicativo_internacao
            atestado_tag.durTrat.valor = atestado.duracao_tratamento
            atestado_tag.indAfast.valor = atestado.indicativo_internacao
            atestado_tag.dscLesao.valor = atestado.descricao_lesao_id.codigo
            if atestado.desc_complementar_lesao:
                atestado_tag.dscCompLesao.valor = atestado.desc_complementar_lesao
            if atestado.diagnostico_provavel:
                atestado_tag.diagProvavel.valor = atestado.diagnostico_provavel
            atestado_tag.codCID.valor = atestado.cod_cid
            if atestado.observacoes:
                atestado_tag.observacao.valor = atestado.observacoes
            atestado_tag.nmEmit.valor = atestado.nome_emitente
            atestado_tag.ideOC.valor = atestado.identidade_orgao_classe
            atestado_tag.nrOC.valor = atestado.num_inscricao_orgao
            if atestado.uf_orgao_classe:
                atestado_tag.ufOC.valor = atestado.uf_orgao_classe

            S2210.evento.cat.atestado.append(atestado_tag)

        if self.hr_comunicacao_acidente_trabalho_id.num_recibo_cat_original:
            catOrigem = pysped.esocial.leiaute.S2210_CatOrigem_2()

            catOrigem.nrRecCatOrig.valor = self.hr_comunicacao_acidente_trabalho_id.num_recibo_cat_original

            S2210.evento.cat.catOrigem.append(catOrigem)

        return S2210, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        self.hr_turnos_trabalho_id.precisa_atualizar = False

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
