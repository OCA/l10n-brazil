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
    _name = b'l10n_br.hr.sefip'

    @api.one
    @api.depends('codigo_recolhimento')
    def _compute_eh_obrigatorio_informacoes_processo(self):
        if self.codigo_recolhimento in ('650', '660'):
            self.eh_obrigatorio_informacoes_processo = True
        else:
            self.eh_obrigatorio_informacoes_processo = False

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
    company_id = fields.Many2one(
        comodel_name='res.company', string=u'Empresa'
    )
    mes = fields.Selection(selection=MESES, string=u'Mês')
    ano = fields.Char(string=u'Ano', size=4)
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
        help="""Campo obrigatório:\n 
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
    eh_obrigatorio_informacoes_processo = fields.Boolean(
        compute='_compute_eh_obrigatorio_informacoes_processo',
        default=False,
    )
    data_geracao = fields.Date(string=u'Data do arquivo')
    # Processo ou convenção coletiva
    num_processo = fields.Char(string=u'Número do processo')
    ano_processo = fields.Char(string=u'Ano do processo', size=4)
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
                ' tam = %s, linha = %s' % (len(linha), linha)
            )

    def _logadouro_bairro_cep_cidade_uf_telefone(self, type, partner_id):
        erro = ''

        if not partner_id.street:
            erro += _("Rua {0} não preenchida\n".format(type))
        if not partner_id.district:
            erro += _("Bairro {0} não preenchido\n".format(type))
        if not partner_id.zip:
            erro += _("Cep {0} não preenchido\n".format(type))
        if not partner_id.city:
            erro += _("Cidade {0} não preenchida\n".format(type))
        if not partner_id.state_id and partner_id.state_id.code:
            erro += _("UF {0} não preenchido\n".format(type))
        if not partner_id.phone:
            # TODO: Pode ser que este campo precise ser revisto por conta da
            # formatação
            erro += _("Telefone {0} não preenchido\n".format(type))
        if not partner_id.number:
            erro += _("Número {0} não preenchido\n".format(type))
        if erro:
            raise ValidationError(erro)

        logadouro = ''
        logadouro += partner_id.street or ''
        logadouro += ' '
        logadouro += partner_id.number or ''
        logadouro += ' '
        logadouro += partner_id.street2 or ''

        return (logadouro, partner_id.district, partner_id.zip,
                partner_id.city, partner_id.state_id.code,
                partner_id.phone)

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
        return self.env['l10n_br.hr.rat.fap'].search(
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

    def _tipo_inscricao_cnae(self, company_id):
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
        return tipo_inscr_empresa, inscr_empresa, cnae

    def _ded_13_lic_maternidade(self):
        """ Registro 12 item 5:

                    Dedução 13o Salário Licença
            Maternidade
            (Informar o valor da parcela de
            13o salário referente ao período
            em que a trabalhadora esteve em
            licença maternidade, nos casos
            em que o
            empregador/contribuinte for
            responsável pelo pagamento do
            salário-maternidade.
            A informação deve ser prestada
            nas seguintes situações:
            - na competência 13, referente ao
            valor pago durante o ano.
            - na competência da rescisão do
            contrato de trabalho (exceto
            rescisão por justa causa),
            aposentadoria sem continuidade
            de vínculo ou falecimento )

            Opcional para a competência 13.
            Opcional para o código de recolhimento 115.
            Opcional para os códigos de recolhimento 150, 155 e 608, quando o CNPJ da empresa for igual ao
            CNPJ do tomador.
            Deve ser informado quando houver movimentação por rescisão de contrato de trabalho (exceto
            rescisão com justa causa), aposentadoria sem continuidade de vínculo, aposentadoria por invalidez
            ou falecimento, para empregada que possuir afastamento por motivo de licença maternidade no ano.
            Não pode ser informado para os códigos de recolhimento 130, 135, 145, 211, 307, 317, 327, 337,
            345, 640, 650, 660 e para empregador doméstico (FPAS 868).
            Não pode ser informado para licença maternidade iniciada a partir de 01/12/1999 e com benefícios
            requeridos até 31/08/2003.
            Não pode ser informado para competências anteriores a 10/1998.
            Não pode ser informado para as competências 01/2001 a 08/2003.
            Sempre que não informado preencher com zeros.

        :return:
        """
        #  TODO:

        return 0.00

    @api.multi
    def gerar_sefip(self):
        for record in self:
            sefip = SEFIP()
            record.sefip = ''
            record.sefip += self._valida_tamanho_linha(
                record._preencher_registro_00(sefip))
            record.sefip += self._valida_tamanho_linha(
                self._preencher_registro_10(sefip))
            for folha in record.env['hr.payslip'].search([
                ('mes_do_ano', '=', record.mes),
                ('ano', '=', record.ano)
            ]).sorted(key=lambda folha: folha.employee_id.pis_pasep):
                record.sefip += self._valida_tamanho_linha(
                    record._preencher_registro_30(sefip, folha))
            record.sefip += self._valida_tamanho_linha(
                sefip._registro_90_totalizador_do_arquivo())
            # self.sefip = sefip._gerar_arquivo_SEFIP()

    def _preencher_registro_00(self, sefip):
        sefip.tipo_inscr_resp = '1' if \
            self.responsible_user_id.parent_id.is_company else '3'
        sefip.inscr_resp = self.responsible_user_id.parent_id.cnpj_cpf
        sefip.nome_resp = self.responsible_user_id.parent_id.legal_name
        sefip.nome_contato = self.responsible_user_id.legal_name or \
            self.responsible_user_id.name
        logadouro, bairro, cep, cidade, uf, telefone = \
            self._logadouro_bairro_cep_cidade_uf_telefone(
                'do responsável', self.responsible_user_id
            )
        sefip.arq_logradouro = logadouro
        sefip.arq_bairro = bairro
        sefip.arq_cep = cep
        sefip.arq_cidade = cidade
        sefip.arq_uf = uf
        sefip.tel_contato = telefone
        sefip.internet_contato = self.responsible_user_id.email
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

    def _preencher_registro_10(self, sefip):

        tipo_inscr_empresa, inscr_empresa, cnae = self._tipo_inscricao_cnae(
            self.company_id
        )

        sefip.tipo_inscr_empresa = tipo_inscr_empresa
        sefip.inscr_empresa = inscr_empresa
        sefip.emp_nome_razao_social = (
            self.company_id.legal_name or self.company_id.name or ''
        )
        logadouro, bairro, cep, cidade, uf, telefone = \
            self._logadouro_bairro_cep_cidade_uf_telefone(
                'da empresa', self.company_id.partner_id
            )
        sefip.emp_logradouro = logadouro
        sefip.emp_bairro = bairro
        sefip.emp_cep = cep
        sefip.emp_cidade = cidade
        sefip.emp_uf = uf
        sefip.emp_tel = telefone
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

        ########
        #
        #
        # TODO: Criar um campo calculado para este registro
        sefip.emp_cod_outras_entidades = self.codigo_outras_entidades
        # TODO: Criar um campo calculado para este registro
        sefip.emp_cod_pagamento_GPS = self.codigo_recolhimento_gps
        # TODO: Criar um campo calculado para este registro
        sefip.emp_percent_isencao_filantropia = ''
        # TODO:
        sefip.emp_salario_familia = ''  # rubrica salario familia
        sefip.emp_salario_maternidade = ''  # soma das li mat pagas no mês
        sefip.emp_contrib_descont_empregados = ''  # total inss retido
        sefip.emp_indic_valor_pos_neg = 0  # Sempre positivo
        sefip.emp_valor_devido_ps_referente = ''
        # valor devido 13 salario,  INSS décimo terceiro igual ao
        # "emp_contrib_descont_empregados" #24

        # TODO: implementação futura / não precisa preencher
        # sefip.emp_banco = self.company_id.bank_id[0].bank
        # sefip.emp_ag = self.company_id.bank_id[0].agency
        # sefip.emp_cc = self.company_id.bank_id[0].account
        return sefip._registro_10_informacoes_empresa()

    def _preencher_registro_12(self, sefip):

        tipo_inscr_empresa, inscr_empresa, cnae = self._tipo_inscricao_cnae(
            self.company_id
        )

        sefip.tipo_inscr_empresa = tipo_inscr_empresa
        sefip.inscr_empresa = inscr_empresa

        # Item 5
        # TODO: Implementar função
        sefip.ded_13_lic_maternidade = self._ded_13_lic_maternidade()

        # Campos da tela
        if self.codigo_recolhimento in ('650', '660'):
            sefip.rec_outras_info_processo = self.num_processo
            sefip.rec_outras_info_processo_ano = self.ano_processo
            sefip.rec_outras_info_vara_JCJ = self.vara_jcj
            sefip.rec_outras_info_periodo_inicio = self.data_inicio
            sefip.rec_outras_info_periodo_fim = self.data_termino

        # Os outros campos são em branco
        return sefip._registro_12_inf_adic_recolhimento_empresa()


    def _preencher_registro_30(self, sefip, folha):
        """
        Acatar categoria 14 e 16 apenas para competências anteriores a 03/2000.
        Acatar categoria 17, 18, 24 e 25 apenas para código de recolhimento 211.
        Acatar categoria 06 apenas para competência maior ou igual a 03/2000.
        Acatar categoria 07 apenas para competência maior ou igual a 12/2000

        Uma linha para cada folha do periodo, sendo rescisão, normal.

        Férias não entra.

        Na competência 13 considerar somente o 13.


        13. Data de opção do FGtS, é sempre a data de contratação!

        16. RB Base do INSS
        17. RB 13 Base do INSS
        ( Na rescisão temos o 16 e o 17!)


        19. Ocorrencia: Acidente de trabalho, rescisão, afastamento por doença
        lic maternidade, ( situaçeõs que o funcionario deixa de trablhlar e o inss
        deverá assumir o pagamento do funcionário)

        20. Verificar se na ABGF, por exemplo, o funcionário esta contratado
        em 2 lugares pois o INSS recolhido em outro lugar pode ter que ser
        informado aqui.

        21. Preenchido somente quando o funcionário esta afastado.
        Geralmente Zerado

        22.
        """

        tipo_inscr_empresa, inscr_empresa, cnae = self._tipo_inscricao_cnae(
            self.company_id
        )
        sefip.tipo_inscr_empresa = tipo_inscr_empresa
        sefip.inscr_empresa = inscr_empresa
        sefip.tipo_inscr_tomador = ' '
        sefip.inscr_tomador = ' ' * 14
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
        # sefip.trabalhador_ocorrencia =
        # sefip.trabalhador_valor_desc_segurado =
        # sefip.trabalhador_remun_base_calc_contribuicao_previdenciaria = folha.wage
        # sefip.trabalhador_base_calc_13_previdencia_competencia =
        # sefip.trabalhador_base_calc_13_previdencia_GPS =
        return sefip._registro_30_registro_do_trabalhador()

    def _preencher_registro_90(self):
        #     sefip = '90'
        #     sefip += '9'*51
        #     sefip += ' '*306
        #     sefip += '*'
        #     sefip += '\n'
        #     return sefip
        pass
