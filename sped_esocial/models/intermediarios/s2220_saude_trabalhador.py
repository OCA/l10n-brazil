# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

import pysped
from openerp import api, models, fields
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialSaudeTrabalhador(models.Model, SpedRegistroIntermediario):
    _name = "sped.hr.saude.trabalhador"

    name = fields.Char(
        related='hr_saude_trabalhador_id.name'
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
        required=True,
    )
    hr_saude_trabalhador_id = fields.Many2one(
        string="Saúde do Trabalhador",
        comodel_name="hr.saude.trabalhador",
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
            'registro': 'S-2220',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtMonit',
            'origem': (
                    'hr.saude.trabalhador,%s' %
                    self.hr_saude_trabalhador_id.id),
            'origem_intermediario': (
                    'sped.hr.saude.trabalhador,%s' % self.id),
        }

        sped_inclusao = self.env['sped.registro'].create(values)
        self.sped_inclusao = [(4, sped_inclusao.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # S-1060
        S2220 = pysped.esocial.leiaute.S2220_2()

        S2220.tpInsc = '1'
        S2220.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
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
            S2220.evento.ideEvento.nrRecibo.valor = \
                registro_para_retificar.recibo
        S2220.evento.ideEvento.indRetif.valor = indRetif
        S2220.evento.ideEvento.tpAmb.valor = int(ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S2220.evento.ideEvento.procEmi.valor = '1'
        S2220.evento.ideEvento.verProc.valor = 'SAB - v8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2220.evento.ideEmpregador.tpInsc.valor = '1'
        S2220.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        S2220.evento.ideVinculo.cpfTrab.valor = limpa_formatacao(
            self.hr_saude_trabalhador_id.contract_id.employee_id.cpf)
        S2220.evento.ideVinculo.nisTrab.valor = limpa_formatacao(
            self.hr_saude_trabalhador_id.contract_id.employee_id.pis_pasep)
        if self.hr_saude_trabalhador_id.contract_id.sped_s2200_id:
            S2220.evento.ideVinculo.matricula.valor = \
                self.hr_saude_trabalhador_id.contract_id.matricula
        if self.hr_saude_trabalhador_id.contract_id.sped_s2300_id:
            S2220.evento.ideVinculo.codCateg.valor = \
                self.hr_saude_trabalhador_id.contract_id.sped.categoria_trabalhador

        S2220.evento.exMedOcup.tpExameOcup.valor = \
            self.hr_saude_trabalhador_id.tipo_exame_ocup

        S2220.evento.exMedOcup.aso.dtAso.valor = \
            self.hr_saude_trabalhador_id.data_aso
        S2220.evento.exMedOcup.aso.resAso.valor = \
            self.hr_saude_trabalhador_id.result_aso
        for exame_aso in self.hr_saude_trabalhador_id.exame_aso_ids:
            exame = pysped.esocial.leiaute.S2220_Exame_2()

            exame.dtExm.valor = exame_aso.data_exame
            exame.procRealizado.valor = exame_aso.procedimento_realizado.codigo
            if exame_aso.obs_procedimento:
                exame.obsProc.valor = exame_aso.obs_procedimento
            exame.ordExame.valor = exame_aso.ordem_exame
            if exame_aso.indicacao_resultado:
                exame.indResult.valor = exame_aso.indicacao_resultado

            S2220.evento.exMedOcup.aso.exame.append(exame)

        if self.hr_saude_trabalhador_id.cpf_medico:
            S2220.evento.exMedOcup.aso.medico.cpfMed.valor = \
                self.hr_saude_trabalhador_id.cpf_medico
        if self.hr_saude_trabalhador_id.nis_medico:
                    S2220.evento.exMedOcup.aso.medico.nisMed.valor = \
                        self.hr_saude_trabalhador_id.nis_medico
        S2220.evento.exMedOcup.aso.medico.nmMed.valor = \
            self.hr_saude_trabalhador_id.nome_medico
        S2220.evento.exMedOcup.aso.medico.nrCRM.valor = \
            self.hr_saude_trabalhador_id.num_crm
        S2220.evento.exMedOcup.aso.medico.ufCRM.valor = \
            self.hr_saude_trabalhador_id.uf_crm

        if self.hr_saude_trabalhador_id.cpf_resp_pcmso:
            S2220.evento.exMedOcup.respMonit.cpfResp.valor = \
                self.hr_saude_trabalhador_id.cpf_resp_pcmso
        S2220.evento.exMedOcup.respMonit.nmResp.valor = \
            self.hr_saude_trabalhador_id.nome_resp_pcmso
        S2220.evento.exMedOcup.respMonit.nrCRM.valor = \
            self.hr_saude_trabalhador_id.num_crm_pcmso
        S2220.evento.exMedOcup.respMonit.ufCRM.valor = \
            self.hr_saude_trabalhador_id.uf_crm_pcmso

        return S2220, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        self.hr_saude_trabalhador_id.precisa_atualizar = False

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
