# -*- coding: utf-8 -*-
# (c) 2017 KMEE INFORMATICA LTDA - Daniel Sadamo <sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import (
    division, print_function, unicode_literals, absolute_import
)

import logging

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError

from .arquivo_sefip import SEFIP
from ..constantes_rh import (MESES, MODALIDADE_ARQUIVO, CODIGO_RECOLHIMENTO,
                             RECOLHIMENTO_GPS, RECOLHIMENTO_FGTS,
                             CENTRALIZADORA, SEFIP_CATEGORIA_TRABALHADOR)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.base import tira_acentos
    from pybrasil import data
except ImportError:
    _logger.info('Cannot import pybrasil')

SEFIP_STATE = [
    ('rascunho', u'Rascunho'),
    ('confirmado', u'Confirmada'),
    ('enviado', u'Enviado'),
]


class L10nBrSefip(models.Model):
    _name = 'l10n_br.hr.sefip'


    @api.one
    @api.depends('codigo_recolhimento', 'codigo_fpas')
    def _compute_eh_obrigatorio_codigo_outras_entidades(self):
        if self.codigo_recolhimento in (
                '115', '130', '135', '150', '155', '211', '608', '650'):
            self.eh_obrigatorio_codigo_outras_entidades = True
        else:
            self.eh_obrigatorio_codigo_outras_entidades = False
            self.codigo_outras_entidades = False
        if self.codigo_fpas == '582':
            self.codigo_outras_entidades = '0'


    state = fields.Selection(selection=SEFIP_STATE, default='rascunho')
    # responsible_company_id = fields.Many2one(
    #     comodel_name='res.company', string=u'Empresa Responsável'
    # )
    responsible_user_id = fields.Many2one(
        comodel_name='res.partner', string=u'Usuário Responsável'
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
    codigo_fpas = fields.Char(
        string=u'Código FPAS',
        default='736',
        required=True,
        help="""• Campo obrigatório.\n 
        • Deve ser um FPAS válido.\n
        • Deve ser diferente de 744 e 779, pois as GPS desses códigos serão  
        geradas automaticamente, sempre que forem informados os respectivos 
        fatos geradores dessas contribuições.\n
        • Deve ser diferente de 620, pois a informação das categorias 15, 16, 
        18, 23 e 25 indica os respectivos fatos geradores dessas 
        contribuições.\n
        • Deve ser diferente de 663 e 671 a partir da competência 04/2004.\n
        • Deve ser igual a 868 para empregador doméstico."""
    )
    eh_obrigatorio_codigo_outras_entidades = fields.Boolean(
        compute='_compute_eh_obrigatorio_codigo_outras_entidades',
    )
    codigo_outras_entidades = fields.Char(
        string=u'Código de outras entidades'
    )
    centralizadora = fields.Selection(
        selection=CENTRALIZADORA,
        string=u'Centralizadora',
        default='1',
        required=True,
        help="""Para indicar as empresas que centralizam o recolhimento 
        do FGTS\n\n
        
        - Deve ser igual a zero (0), para os códigos de recolhimento 
            130, 135, 150, 155, 211, 317, 337, 608 e para empregador doméstico
             (FPAS 868).\n
        - Quando existir empresa centralizadora deve existir, no mínimo,
         uma empresa centralizada e vice-versa.\n
        - Quando existir centralização, as oito primeiras posições\n 
        do CNPJ da centralizadora e da centralizada devem ser iguais.\n
        - Empresa com inscrição CEI não possui centralização.\n"""
    )
    data_geracao = fields.Date(string=u'Data do arquivo')
    #Processo ou convenção coletiva
    num_processo = fields.Char(string=u'Número do processo')
    ano_processo = fields.Char(string=u'Ano do processo')
    vara_jcj = fields.Char(string=u'Vara/JCJ')
    data_inicio = fields.Date(string=u'Data de Início')
    data_termino = fields.Date(string=u'Data de término')
    sefip = fields.Text(
        string=u'Prévia do SEFIP'
    )

    def _valida_tamanho_linha(self, linha):
        """Valida tamanho da linha (sempre igual a 360 posições) e
         adiciona quebra caso esteja correto"""
        if len(linha) == 360:
            return linha + '\n'
        else:
            raise ValidationError(
                'Tamanho da linha diferente de 360 posicoes.'
                ' tam = %s, linha = %s' %(len(linha), linha)
            )

    @api.multi
    def gerar_sefip(self):
        sefip = SEFIP()
        self.sefip = ''
        self.sefip += self._valida_tamanho_linha(self._preencher_registro_00(sefip))
        # self._preencher_registro_10(sefip)
        for folha in self.env['hr.payslip'].search([
                ('mes_do_ano', '=', self.mes),
                ('ano', '=', self.ano)
                ]).sorted(key=lambda folha: folha.employee_id.pis_pasep):
            self.sefip += self._valida_tamanho_linha(self._preencher_registro_30(sefip, folha))
        self.sefip += self._valida_tamanho_linha(sefip._registro_90_totalizador_do_arquivo())
        # self.sefip = sefip._gerar_arquivo_SEFIP()

    # def _registro_00(self):
    #     _validar = self._validar
    #     sefip = '00'                        # Tipo de Registro
    #     sefip += _validar('', 51, 'AN')     # Brancos
    #     sefip += _validar('1', 1, 'N')      # Tipo de Remessa
    #     sefip += '1' if self.responsible_user_id.is_company \
    #         else '3'                        # Tipo de Inscrição - Responsável
    #     sefip += _validar(
    #         self.responsible_user_id.cnpj_cpf, 14, 'N'
    #     )                                   # Inscrição do Responsável
    #     sefip += _validar(
    #         self.responsible_user_id.legal_name, 30, 'AN'
    #     )                                   # Razão Social
    #     sefip += _validar(
    #         self.responsible_user_id.name, 20, 'A'
    #     )                                   # Nome Pessoa Contato
    #     logradouro = _validar(self.responsible_user_id.street, 0, '') + ' '
    #     logradouro += _validar(self.responsible_user_id.number, 0, '') + ' '
    #     logradouro += _validar(self.responsible_user_id.street2, 0, '')
    #     sefip += _validar(
    #         logradouro, 50, 'AN'
    #     )                                   # Logradouro
    #     sefip += _validar(
    #         self.responsible_user_id.district, 20, 'AN'
    #     )                                   # Bairro
    #     sefip += _validar(
    #         self.responsible_user_id.zip, 8, 'N'
    #     )                                   # CEP
    #     sefip += _validar(
    #         self.responsible_user_id.l10n_br_city_id, 20, 'AN'
    #     )                                   # Cidade
    #     sefip += _validar(
    #         self.responsible_user_id.state_id.code, 2, 'N'
    #     )                                   # UF
    #     sefip += _validar(
    #         self.responsible_user_id.phone, 12, 'N'
    #     )                                   # Telefone
    #     sefip += _validar(
    #         self.responsible_user_id.website, 60, 'AN'
    #     )                                   # Site
    #     sefip += _validar(self.ano, 4, 'N') + \
    #         _validar(self.mes, 2, 'N')      # Competência
    #     sefip += _validar(
    #         self.codigo_recolhimento, 3, 'N'
    #     )                                   # Código de Recolhimento
    #     sefip += _validar(
    #         self.recolhimento_fgts, 1, 'N'
    #     )                                   # Recolhimento FGTS
    #     sefip += _validar(
    #         self.modalidade_arquivo, 1, 'N'
    #     )                                   # Modalidade do Arquivo
    #     sefip += _validar(
    #         fields.Datetime.from_string(
    #             self.data_recolhimento_fgts).strftime('%d%m%Y'), 8, 'D'
    #     )                                   # Data de Recolhimento do FGTS
    #     sefip += _validar(
    #         self.recolhimento_gps, 1, 'N'
    #     )                                   # Indicador de Recolhimento PS
    #     sefip += _validar(
    #         fields.Datetime.from_string(
    #             self.data_recolhimento_gps).strftime('%d%m%Y'), 8, 'D'
    #     )                                   # Data de Recolhimento PS
    #     sefip += _validar(
    #         '', 7, 'N'
    #     )                                   # Índice de Recolhimento em Atraso
    #     sefip += '1' if self.company_id.supplier_partner_id.is_company \
    #         else '3'                    # Tipo de Inscrição do Fornecedor
    #     sefip += _validar(
    #         self.company_id.supplier_partner_id.cnpj_cpf, 14, 'N'
    #     )                               # Inscrição do Fornecedor
    #     sefip += _validar('', 18, 'AN')
    #     sefip += '*'
    #     sefip += '\n'
    #     return sefip

    def _preencher_registro_00(self, sefip):
        sefip.tipo_inscr_resp = '1' if self.responsible_user_id.is_company \
            else '3'
        sefip.inscr_resp = self.responsible_user_id.cnpj_cpf
        sefip.nome_resp = self.responsible_user_id.parent_id.name
        sefip.nome_contato = self.responsible_user_id.name
        sefip.arq_logradouro = self.responsible_user_id.street or '' + ' ' + \
                               self.responsible_user_id.number or ''+ ' ' + \
                               self.responsible_user_id.street2 or ''
        sefip.arq_bairro = self.responsible_user_id.district
        sefip.arq_cep = self.responsible_user_id.zip
        sefip.arq_cidade = self.responsible_user_id.l10n_br_city_id.name
        sefip.arq_uf = self.responsible_user_id.state_id.code
        sefip.tel_contato = self.responsible_user_id.phone
        sefip.internet_contato = self.responsible_user_id.website
        sefip.competencia = self.ano + self.mes
        sefip.cod_recolhimento = self.codigo_recolhimento
        sefip.indic_recolhimento_fgts = self.recolhimento_fgts
        sefip.modalidade_arq = self.modalidade_arquivo
        sefip.data_recolhimento_fgts = fields.Datetime.from_string(
            self.data_recolhimento_fgts).strftime('%d%m%Y') \
            if self.data_recolhimento_fgts else ''
        sefip.indic_recolh_ps = self.recolhimento_gps
        sefip.data_recolh_ps = fields.Datetime.from_string(
            self.data_recolhimento_gps).strftime('%d%m%Y') \
            if self.data_recolhimento_fgts else ''
        sefip.tipo_inscr_fornec = (
            '1' if self.company_id.supplier_partner_id.is_company else '3')
        sefip.inscr_fornec = self.company_id.supplier_partner_id.cnpj_cpf
        return sefip._registro_00_informacoes_responsavel()

    # def _registro_10(self):
    #     _validar = self._validar
    #     sefip = '10'                        # Tipo de Registro
    #     sefip += '1'                        # Tipo de Inscrição - Empresa
    #     sefip += _validar(
    #         self.company_id.cnpj_cpf, 14, 'N'
    #     )                                   # Inscrição do Empresa
    #     sefip += '0'*36                     # Zeros
    #     sefip += _validar(
    #         self.company_id.legal_name, 40, 'AN'
    #     )                                   # Razão Social
    #     logradouro = _validar(self.company_id.street, 0, '') + ' '
    #     logradouro += _validar(self.company_id.number, 0, '') + ' '
    #     logradouro += _validar(self.company_id.street2, 0, '')
    #     sefip += _validar(
    #         logradouro, 50, 'AN'
    #     )                                   # Logradouro
    #     sefip += _validar(
    #         self.company_id.district, 20, 'AN'
    #     )                                   # Bairro
    #     sefip += _validar(
    #         self.company_id.zip, 8, 'N'
    #     )                                   # CEP
    #     sefip += _validar(
    #         self.company_id.l10n_br_city_id, 20, 'AN'
    #     )                                   # Cidade
    #     sefip += _validar(
    #         self.company_id.state_id.code, 2, 'N'
    #     )                                   # UF
    #     sefip += _validar(
    #         self.company_id.phone, 12, 'N'
    #     )                                   # Telefone
    #     sefip += 'N'                        # Indicador Alteração Endereço
    #     sefip += _validar(
    #         self.company_id.cnae, 7, 'N'
    #     )                                   # CNAE
    #     sefip += 'N'                        # Indicação de Alteração do CNAE
    #     sefip += _validar(self.env['l10n_br.hr.rat.fap'].search([
    #         ('year', '=', self.ano)], limit=1
    #     ).rat_rate, 2, 'V') or '00'         # Alíquota RAT
    #     sefip += self.centralizadora        # Código de Centralização
    #     sefip += '1'                        # SIMPLES
    #     sefip += self.codigo_fpas           # FPAS
    #     sefip += '0003'                     # Código de Outras Entidades
    #     sefip += '2100'                     # Código de Pagamento GPS
    #     sefip += '     '                    # Percentual de Isenção Filantropia
    #     sefip += _validar('', 15, 'N')      # Salário-família
    #     sefip += _validar('', 15, 'N')      # Salário-maternidade
    #     sefip += '0'*15                     # Contrib. Desc. Empregado
    #     sefip += '0'                        # Indicador de positivo ou negativo
    #     sefip += '0'*14                     # Valor devido à previdência social
    #     sefip += ' '*16                     # Banco
    #     sefip += '0'*45                     # Zeros
    #     sefip += ' '*4                      # Brancos
    #     sefip += '*'
    #     sefip += '\n'
    #     return sefip

    def _rat(self):
        """
        - Campo obrigatório.
        - Campo com uma posição inteira e uma decimal.
        - Campo obrigatório para competência maior ou igual a 10/1998.
        - Não pode ser informado para competências anteriores a 10/1998.
        - Não pode ser informado para competências anteriores a 04/99
            quando o FPAS for 639.
        - Não pode ser informado para os códigos de recolhimento
            145, 307, 317, 327, 337, 345, 640 e 660.
        - Será zeros para FPAS 604, 647, 825, 833 e 868 (empregador doméstico)
            e para a empresa optante pelo SIMPLES.
        - Não pode ser informado para FPAS 604 com recolhimento de código 150
         em competências posteriores a 10/2001.

            Sempre que não informado o campo deve ficar em branco.

        :return:
        """

        if self.codigo_recolhimento in (
                '145', '307', '317', '327', '337', '345', '640', '660'):
            return ''
        elif (self.codigo_recolhimento in (
                '604', '647', '825', '833', '868') or
              self.company_id.fiscal_type in ('1', '2')):
            return 0.00
        elif self.codigo_fpas == '604' and self.codigo_recolhimento == '150':
            return ''
        return self.env['l10n_hr.rat.fap'].search(
            [('year', '=', self.ano)], limit=1).rat_rate or '0'

    def _simples(self):
        """
        Campo obrigatório.
        Só pode ser:
            1 - Não Optante;
            2 – Optante;
            3 – Optante - faturamento anual superior a R$1.200.000,00 ;
            4 – Não Optante - Produtor Rural Pessoa Física (CEI e FPAS 604 )
            com faturamento anual superior a R$1.200.000,00.
            5 – Não Optante – Empresa com Liminar para não recolhimento da
            Contribuição Social – Lei Complementar 110/01, de 26/06/2001.
            6 – Optante - faturamento anual superior a R$1.200.000,00 -
            Empresa com Liminar para não recolhimento da Contribuição
            Social – Lei Complementar 110/01, de 26/06/2001.
        Deve sempre ser igual a 1 ou 5 para
            FPAS 582, 639, 663, 671, 680 e 736.
        Deve sempre ser igual a 1 para o FPAS 868 (empregador doméstico).

        Não pode ser informado para o código de recolhimento 640.
        Não pode ser informado para competência anterior a 12/1996.

        Os códigos 3, 4, 5 e 6 não podem ser informados a partir da
        competência 01/2007.

        Sempre que não informado o campo deve ficar em branco.
        """
        # TODO: Melhorar esta função para os outros casos de uso
        if self.company_id.fiscal_type == '3':
            return '1'
        else:
            return '2'

    def _preencher_registro_10(self, sefip):

        if self.company_id.partner_id.is_company:
            tipo_inscr_empresa = '1'
            inscr_empresa = self.company_id.cnpj_cpf
            cnae = self.company_id.cnae
        else:
            raise ValidationError(_(
                'Exportação de empregador doméstico não parametrizada '
                'corretamente'))
            tipo_inscr_empresa = '0'
            # TODO: Campo não implementado
            inscr_empresa = self.company_id.cei
            cnae = self.company_id.cnae
            if '9700500' not in cnae:
                raise ValidationError(_(
                    'Para empregador doméstico utilizar o número 9700500.'
                ))


        sefip.tipo_inscr_empresa = tipo_inscr_empresa
        sefip.inscr_empresa = inscr_empresa
        sefip.emp_nome_razao_social = (
            self.company_id.legal_name or self.company_id.name or ''
        )
        sefip.emp_logradouro = self.company_id.street or '' + ' ' + \
                               self.company_id.number or '' + ' ' + \
                               self.company_id.street2 or ''
        sefip.emp_bairro = self.company_id.district or ''
        sefip.emp_cep = self.company_id.zip or ''
        sefip.emp_cidade = self.company_id.city
        sefip.emp_uf = self.company_id.state_id.code
        # TODO: Pode ser que este campo precise ser revisto por conta da
        # formatação
        sefip.emp_tel = self.company_id.phone
        #
        # A responsabilidade de alteração do enderço da empresa deve ser
        # sempre feita pela receita federal, não ousamos usar esta campo.
        #
        sefip.emp_indic_alteracao_endereco = 'N'

        sefip.emp_cnae = cnae
        # sefip.emp_indic_alteracao_cnae = 'n'
        sefip.emp_aliquota_RAT = self._rat()
        sefip.emp_cod_centralizacao = self.centralizadora
        sefip.emp_simples = self._simples()
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


    # def _registro_30(self, folha):
    #     _validar = self._validar
    #     sefip = '30'                        # Tipo de Registro
    #     sefip += '1'                        # Tipo de Inscrição - Empresa
    #     sefip += _validar(
    #         self.company_id.cnpj_cpf, 14, 'N'
    #     )                                   # Inscrição Empresa
    #     sefip += ' '                        # Tipo Inscrição Tomador/Obra
    #     sefip += ' '*14                     # Inscrição Tomador/Obra
    #     sefip += _validar(
    #         folha.employee_id.pis_pasep, 11, 'N'
    #     )                                   # PIS/PASEP
    #     sefip += _validar(
    #         folha.contract_id.date_start, 8, 'D'
    #     )                                   # Data de Admissão
    #     sefip += '01'                       # Categoria Trabalhador
    #     sefip += _validar(
    #         folha.employee_id.name, 70, 'A'
    #     )                                   # Nome Trabalhador
    #     sefip += _validar(
    #         folha.employee_id.registration, 11, 'N'
    #     )                                   # Matrícula Trabalhador
    #     sefip += _validar(
    #         folha.employee_id.ctps, 7, 'N'
    #     )                                   # Número CTPS
    #     sefip += _validar(
    #         folha.employee_id.ctps_series, 5, 'N'
    #     )                                   # Série CTPS
    #     sefip += _validar(
    #         folha.contract_id.date_start
    #     )                                   # Data Opção FGTS
    #     sefip += _validar(
    #         folha.employee_id.birthday, 8, 'D'
    #     )                                   # Data de Nascimento
    #     sefip += _validar(
    #         folha.contract_id.job_id.cbo_id.code, 5, 'N'
    #     )                                   # CBO
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Remuneração sem 13º
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Remuneração 13º
    #     sefip += _validar(
    #         '', 2, 'AN'
    #     )                                   # Classe de Contribuição (errado)
    #     sefip += _validar(
    #         '', 2, 'AN'
    #     )                                   # Ocorrência
    #     sefip += _validar(
    #         '', 15, 'N'
    #     )                                   # Valor descontado do segurado ocorrencia 05
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Base de Cálculo Contr. Prev. (errado)
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Base de Cálculo 13º - 1 (errado)
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Base de Cálculo 13º - 2 (errado)
    #     sefip += _validar(
    #         '', 98, 'AN'
    #     )                                   # Brancos
    #     sefip += '*'
    #     sefip += '\n'
    #     return sefip


    def _preencher_registro_30(self, sefip, folha):
        sefip.tipo_inscr_empresa = '1'
        sefip.inscr_empresa = self.company_id.cnpj_cpf
        sefip.tipo_inscr_tomador = ' '
        sefip.inscr_tomador = ' '*14
        sefip.pis_pasep_ci = folha.employee_id.pis_pasep
        sefip.data_admissao = folha.contract_id.date_start
        sefip.categoria_trabalhador = SEFIP_CATEGORIA_TRABALHADOR.get(
            folha.contract_id.categoria, '01')
        sefip.nome_trabalhador = folha.employee_id.name
        sefip.matricula_trabalhador = folha.employee_id.registration
        sefip.num_ctps = folha.employee_id.ctps
        sefip.serie_ctps = folha.employee_id.ctps_series
        # sefip.data_de_opcao =
        sefip.data_de_nascimento = folha.employee_id.birthday
        sefip.trabalhador_cbo = folha.contract_id.job_id.cbo_id.code
        # sefip.trabalhador_remun_sem_13 = holerite.salario-total
        # sefip.trabalhador_remun_13 =
        # sefip.trabalhador_classe_contrib =
        # ONDE SE ENCONTRAM INFORMAÇÕES REFERENTES A INSALUBRIDADE, DEVERIAM ESTAR NO CAMPO job_id?
        #sefip.trabalhador_ocorrencia =
        # sefip.trabalhador_valor_desc_segurado =
        # sefip.trabalhador_remun_base_calc_contribuicao_previdenciaria = folha.wage
        # sefip.trabalhador_base_calc_13_previdencia_competencia =
        # sefip.trabalhador_base_calc_13_previdencia_GPS =
        return sefip._registro_30_registro_do_trabalhador()

    # def _preencher_registro_90(self):
    #     sefip = '90'
    #     sefip += '9'*51
    #     sefip += ' '*306
    #     sefip += '*'
    #     sefip += '\n'
    #     return sefip
