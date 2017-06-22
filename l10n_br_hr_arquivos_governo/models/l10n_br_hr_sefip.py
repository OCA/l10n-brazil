# -*- coding: utf-8 -*-
# (c) 2017 KMEE INFORMATICA LTDA - Daniel Sadamo <sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models
from ..constantes_rh import (MESES, MODALIDADE_ARQUIVO, CODIGO_RECOLHIMENTO,
                             RECOLHIMENTO_GPS, RECOLHIMENTO_FGTS,
                             CENTRALIZADORA)

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
        sefip.arq_uf = self.responsible_user_id.state.code
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

        return sefip._registro_10_informacoes_empresa()
