# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

import pysped
from openerp import api, models, fields
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialCondicaoAmbienteTrabalho(models.Model, SpedRegistroIntermediario):
    _name = "sped.hr.condicao.ambiente.trabalho"

    name = fields.Char(
        related='hr_condicao_ambiente_trabalho_id.name'
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
        required=True,
    )
    hr_condicao_ambiente_trabalho_id = fields.Many2one(
        string="Condição Ambiente de Trabalho",
        comodel_name="hr.condicao.ambiente.trabalho",
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
            'registro': 'S-2240',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'infoExpRisco',
            'origem': (
                    'hr.condicao.ambiente.trabalho,%s' %
                    self.hr_condicao_ambiente_trabalho_id.id),
            'origem_intermediario': (
                    'sped.hr.condicao.ambiente.trabalho,%s' % self.id),
        }

        sped_inclusao = self.env['sped.registro'].create(values)
        self.sped_inclusao = [(4, sped_inclusao.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # S-1060
        S2240 = pysped.esocial.leiaute.S2240_2()

        S2240.tpInsc = '1'
        S2240.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
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
            S2240.evento.ideEvento.nrRecibo.valor = \
                registro_para_retificar.recibo
        S2240.evento.ideEvento.indRetif.valor = indRetif
        S2240.evento.ideEvento.tpAmb.valor = int(ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S2240.evento.ideEvento.procEmi.valor = '1'
        S2240.evento.ideEvento.verProc.valor = 'SAB - v8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2240.evento.ideEmpregador.tpInsc.valor = '1'
        S2240.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        S2240.evento.ideVinculo.cpfTrab.valor = limpa_formatacao(
            self.hr_condicao_ambiente_trabalho_id.contract_id.employee_id.cpf)
        S2240.evento.ideVinculo.nisTrab.valor = limpa_formatacao(
            self.hr_condicao_ambiente_trabalho_id.contract_id.employee_id.pis_pasep)
        if self.hr_condicao_ambiente_trabalho_id.contract_id.sped_s2200_id:
            S2240.evento.ideVinculo.matricula.valor = \
                self.hr_condicao_ambiente_trabalho_id.contract_id.matricula
        if self.hr_condicao_ambiente_trabalho_id.contract_id.sped_s2300_id:
            S2240.evento.ideVinculo.codCateg.valor = \
                self.hr_condicao_ambiente_trabalho_id.contract_id.categoria

        S2240.evento.infoExpRisco.dtIniCondicao.valor = \
            self.hr_condicao_ambiente_trabalho_id.inicio_condicao

        for ambiente in self.hr_condicao_ambiente_trabalho_id.hr_ambiente_ids:
            info_amb = pysped.esocial.leiaute.S2240_InfoAmb_2()
            info_amb.codAmb.valor = ambiente.cod_ambiente

            S2240.evento.infoExpRisco.infoAmb.append(info_amb)

        S2240.evento.infoExpRisco.infoAtiv.dscAtivDes.valor = \
            self.hr_condicao_ambiente_trabalho_id.hr_atividade_id.desc_atividade
        for cod_atividade in self.hr_condicao_ambiente_trabalho_id.hr_atividade_id.cod_atividade_ids:
            atividade_periculosidade = \
                pysped.esocial.leiaute.S2240_AtivPericInsal_2()
            atividade_periculosidade.codAtiv.valor = cod_atividade.codigo

            S2240.evento.infoExpRisco.infoAtiv.ativPericInsal.append(
                atividade_periculosidade)

        for fator_risco in \
                self.hr_condicao_ambiente_trabalho_id.hr_fator_risco_ids:
            fatrisc = pysped.esocial.leiaute.S2240_FatRisco_2()

            fatrisc.codFatRis.valor = fator_risco.cod_fator_risco_id.codigo
            if fator_risco.dsc_fat_risco:
                fatrisc.dscFatRisc.valor = fator_risco.dsc_fat_risco
            fatrisc.tpAval.valor = fator_risco.tp_avaliacao
            if fator_risco.intensidade_concentracao:
                fatrisc.intConc.valor = \
                    fator_risco.intensidade_concentracao
            if fator_risco.limite_tolerancia:
                fatrisc.limTol.valor = \
                    fator_risco.limite_tolerancia
            if fator_risco.unidade_medida:
                fatrisc.unMed.valor = \
                    fator_risco.unidade_medida
            if fator_risco.tec_medicao:
                fatrisc.tecMedicao.valor = \
                    fator_risco.tec_medicao
            fatrisc.insalubridade.valor = \
                fator_risco.insalubridade
            fatrisc.periculosidade.valor = \
                fator_risco.periculosidade
            if self.hr_condicao_ambiente_trabalho_id.contract_id.sped_s2200_id and self.hr_condicao_ambiente_trabalho_id.contract_id.tp_reg_prev == '1' and not self.hr_condicao_ambiente_trabalho_id.contract_id.categoria == '104':
                fatrisc.aposentEsp.valor = \
                    fator_risco.aposentadoria_especial
            if self.hr_condicao_ambiente_trabalho_id.contract_id.sped_s2300_id and self.hr_condicao_ambiente_trabalho_id.contract_id.categoria in ['201', '202', '731', '734', '738']:
                fatrisc.aposentEsp.valor = \
                    fator_risco.aposentadoria_especial

            fatrisc.epcEpi.utilizEPC.valor = fator_risco.epc_id.utilizacao_epc
            if fator_risco.epc_id.eficiencia_epc:
                fatrisc.epcEpi.eficEpc.valor = fator_risco.epc_id.eficiencia_epc
            fatrisc.epcEpi.utilizEPI.valor = fator_risco.epc_id.utilizacao_epi

            for epi in fator_risco.epc_id.epi_ids:
                epi_tag = pysped.esocial.leiaute.S2240_Epi_2()

                epi_tag.caEPI.valor = epi.certificado_aprovacao
                epi_tag.dscEPI.valor = epi.desc_epi
                epi_tag.eficEpi.valor = epi.eficiencia_epi
                epi_tag.medProtecao.valor = epi.med_protecao_coletiva
                epi_tag.condFuncto.valor = epi.cond_funcionamento
                epi_tag.usoInint.valor = epi.uso_ininterrupto
                epi_tag.przValid.valor = epi.prazo_validade_certificado_epi
                epi_tag.periodicTroca.valor = epi.periodicidade_troca
                epi_tag.higienizacao.valor = epi.higienizacao

                fatrisc.epcEpi.epi.append(epi_tag)

            S2240.evento.infoExpRisco.fatRisco.append(fatrisc)

        for responsavel in self.hr_condicao_ambiente_trabalho_id.hr_responsavel_ambiente_ids:
            resp_reg = pysped.esocial.leiaute.S2240_RespReg_2()

            resp_reg.cpfResp.valor = responsavel.cpf_responsavel
            resp_reg.nisResp.valor = responsavel.nis_responsavel
            resp_reg.nmResp.valor = responsavel.nome
            resp_reg.ideOC.valor = responsavel.identificacao_ordem_classe
            if responsavel.descricao_ordem_classe:
                resp_reg.dscOC.valor = responsavel.descricao_ordem_classe
            resp_reg.nrOC.valor = responsavel.num_inscricao
            resp_reg.ufOC.valor = responsavel.uf

            S2240.evento.infoExpRisco.respReg.append(resp_reg)

        if self.hr_condicao_ambiente_trabalho_id.metodologia_erg or \
                self.hr_condicao_ambiente_trabalho_id.obs_complementares:
            obs_met = pysped.esocial.leiaute.S2240_Obs_2()

            if self.hr_condicao_ambiente_trabalho_id.metodologia_erg:
                obs_met.metErg.valor = \
                    self.hr_condicao_ambiente_trabalho_id.metodologia_erg
            else:
                obs_met.obsCompl.valor = \
                    self.hr_condicao_ambiente_trabalho_id.obs_complementares

            S2240.evento.infoExpRisco.obs.append(obs_met)

        return S2240, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        self.hr_condicao_ambiente_trabalho_id.precisa_atualizar = False

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
