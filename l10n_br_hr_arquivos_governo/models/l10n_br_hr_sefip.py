# -*- coding: utf-8 -*-
# (c) 2017 KMEE INFORMATICA LTDA - Daniel Sadamo <sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models
from ..constantes_rh import (MESES, MODALIDADE_ARQUIVO, CODIGO_RECOLHIMENTO,
                             RECOLHIMENTO_GPS, RECOLHIMENTO_FGTS,
                             CENTRALIZADORA, SEFIP_CATEGORIA_TRABALHADOR)

SEFIP_STATE = [
    ('rascunho',u'Rascunho'),
    ('confirmado',u'Confirmada'),
    ('enviado',u'Enviado'),
]


class L10nBrSefip(models.Model):
    _name = 'l10n_br.hr.sefip'

    state = fields.Selection(selection=SEFIP_STATE, default='rascunho')
    # responsible_company_id = fields.Many2one(
    #     comodel_name='res.company', string=u'Empresa Responsável'
    # )
    responsible_user_id = fields.Many2one(
        comodel_name='res.users', string=u'Usuário Responsável'
    )
    company_id = fields.Many2one(comodel_name='res.company', string=u'Empresa')
    mes = fields.Selection(selection=MESES, string=u'Mês')
    ano = fields.Char(string=u'Ano')
    modalidade_arquivo = fields.Selection(
        selection=MODALIDADE_ARQUIVO, string=u'Modalidade do arquivo'
    )
    codigo_recolhimento = fields.Selection(
        string=u'Código de recolhimento', selection=CODIGO_RECOLHIMENTO
    )
    recolhimento_fgts = fields.Selection(
        string=u'Recolhimento do FGTS', selection=RECOLHIMENTO_FGTS
     )
    data_recolhimento_fgts = fields.Date(
        string=u'Data de recolhimento do FGTS'
    )
    codigo_recolhimento_gps = fields.Char(
        string=u'Código de recolhimento do GPS'
    )
    recolhimento_gps = fields.Selection(
        string=u'Recolhimento do GPS', selection=RECOLHIMENTO_GPS
    )
    data_recolhimento_gps = fields.Date(
        string=u'Data de recolhimento do GPS'
    )
    codigo_fpas = fields.Char(string=u'Código FPAS')
    codigo_outras_entidades = fields.Char(string=u'Código de outras entidades')
    centralizadora = fields.Selection(
        selection=CENTRALIZADORA, string=u'Centralizadora'
    )
    data_geracao = fields.Date(string=u'Data do arquivo')
    #Processo ou convenção coletiva
    num_processo = fields.Char(string=u'Número do processo')
    ano_processo = fields.Char(string=u'Ano do processo')
    vara_jcj = fields.Char(string=u'Vara/JCJ')
    data_inicio = fields.Date(string=u'Data de Início')
    data_termino = fields.Date(string=u'Data de término')

    def _preencher_registro_00(self, sefip):
        sefip.tipo_inscr_resp = '1' if self.responsible_user_id.is_company \
            else '3'
        sefip.inscr_resp = self.responsible_user_id.cnpj_cpf
        sefip.nome_resp = self.responsible_user_id.parent_id.name
        sefip.nome_contato = self.responsible_user_id.name
        sefip.arq_logradouro = self.responsible_user_id.street + ' ' + \
                               self.responsible_user_id.number + ' ' + \
                               self.responsible_user_id.street2
        sefip.arq_bairro = self.responsible_user_id.district
        sefip.arq_cep = self.responsible_user_id.zip
        sefip.arq_cidade = self.responsible_user_id.l10n_br_city.name
        sefip.arq_uf = self.responsible_user_id.state_id.code
        sefip.tel_contato = self.responsible_user_id.phone
        sefip.internet_contato = self.responsible_user_id.website
        sefip.competencia = self.ano + self.mes
        sefip.cod_recolhimento = self.codigo_recolhimento
        sefip.indic_recolhimento_fgts = self.recolhimento_fgts
        sefip.modalidade_arq = self.modalidade_arquivo
        sefip.data_recolhimento_fgts = self.data_recolhimento_fgts
        sefip.indic_recolh_ps = self.recolhimento_gps
        sefip.data_recolh_ps = self.data_recolhimento_gps
        sefip.tipo_inscr_fornec = (
            '1' if self.company_id.supplier_partner_id.is_company else '3')
        sefip.inscr_fornec = self.company_id.supplier_partner_id.cnpj_cpf
        return sefip._registro_00_informacoes_responsavel()

    def _preencher_registro_10(self, sefip):
        aliquota_rat = self.env['l10n_hr.rat.fap'].search(
            [('year', '=', self.ano)], limit=1).rat_rate or '0'
        # sefip.tipo_inscr_empresa = self.
        sefip.inscr_empresa = self.company_id.cnpj_cei
        sefip.emp_nome_razao_social = self.company_id.name
        sefip.emp_logradouro = self.company_id.street + ' ' + \
                               self.company_id.number + ' ' + \
                               self.company_id.street2
        sefip.emp_bairro = self.company_id.district
        sefip.emp_cep = self.company_id.zip
        sefip.emp_cidade = self.company_id.l10n_br_city.name
        sefip.emp_uf = self.company_id.state_id.code
        sefip.emp_tel = self.company_id.phone
        # sefip.emp_indic_alteracao_endereco = 'n'
        sefip.emp_cnae = self.company_id.cnae
        # sefip.emp_indic_alteracao_cnae = 'n'
        sefip.emp_aliquota_RAT = aliquota_rat
        sefip.emp_cod_centralizacao = self.centralizadora
        sefip.emp_simples = '1' if self.company_id.fiscal_type == '3' else '2'
        sefip.emp_FPAS = self.codigo_fpas
        sefip.emp_cod_outras_entidades = self.codigo_outras_entidades
        sefip.emp_cod_pagamento_GPS = self.codigo_recolhimento_gps
        # sefip.emp_percent_isencao_filantropia = self.
        # sefip.emp_salario_familia =
        # sefip.emp_salario_maternidade =
        # sefip.emp_banco = self.company_id.bank_id[0].bank
        # sefip.emp_ag = self.company_id.bank_id[0].agency
        # sefip.emp_cc = self.company_id.bank_id[0].account
        return sefip._registro_10_informacoes_empresa()

    def _preencher_registro_30(self, sefip, contract):
        # sefip.tipo_inscr_empresa =
        sefip.inscr_empresa = self.company_id.cnpj_cei
        # sefip.tipo_inscr_tomador = self.
        # sefip.inscr_tomador = self
        sefip.pis_pasep_ci = contract.employee_id.pis_pasep
        sefip.data_admissao = contract.date_start
        sefip.categoria_trabalhador = SEFIP_CATEGORIA_TRABALHADOR.get(
            contract.categoria, '01')
        sefip.nome_trabalhador = contract.employee_id.name
        sefip.matricula_trabalhador = contract.employee_id.registration
        sefip.num_ctps = contract.employee_id.ctps
        sefip.serie_ctps = contract.employee_id.ctps_series
        # sefip.data_de_opcao =
        sefip.data_de_nascimento = contract.employee_id.birthday
        sefip.trabalhador_cbo = contract.job_id.cbo_id.code
        # sefip.trabalhador_remun_sem_13 = holerite.salario-total
        # sefip.trabalhador_remun_13 =
        # sefip.trabalhador_classe_contrib =
        # ONDE SE ENCONTRAM INFORMAÇÕES REFERENTES A INSALUBRIDADE, DEVERIAM ESTAR NO CAMPO job_id?
        #sefip.trabalhador_ocorrencia =
        # sefip.trabalhador_valor_desc_segurado =
        sefip.trabalhador_remun_base_calc_contribuicao_previdenciaria = contract.wage
        sefip.trabalhador_base_calc_13_previdencia_competencia =
        sefip.trabalhador_base_calc_13_previdencia_GPS =