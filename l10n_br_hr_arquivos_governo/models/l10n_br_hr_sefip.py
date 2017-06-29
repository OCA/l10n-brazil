# -*- coding: utf-8 -*-
# (c) 2017 KMEE INFORMATICA LTDA - Daniel Sadamo <sadamo@kmee.com.br>
# (c) 2017 KMEE INFORMATICA LTDA - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import (
    division, print_function, unicode_literals, absolute_import
)

import logging
import base64
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError

from openerp.addons.l10n_br_base.tools.misc import punctuation_rm

from .arquivo_sefip import SEFIP
from ..constantes_rh import (
    MESES, MODALIDADE_ARQUIVO, CODIGO_RECOLHIMENTO, RECOLHIMENTO_GPS,
    RECOLHIMENTO_FGTS, CENTRALIZADORA, OCORRENCIA_SEFIP,
)

_logger = logging.getLogger(__name__)

SEFIP_STATE = [
    ('rascunho', u'Rascunho'),
    ('confirmado', u'Confirmada'),
    ('enviado', u'Enviado'),
]


class L10nBrSefip(models.Model):
    _name = b'l10n_br.hr.sefip'

    @api.multi
    def name_get(self):
        result = []
        meses = dict(MESES)
        for record in self:
            name = (self.company_id.name + ' ' + meses.get(self.mes) +
                    '/' + self.ano + ' - Recolhimento: ' +
                    self.codigo_recolhimento)
            result.append((record.id, name))
        return result

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

    @api.multi
    def _retornar_valor_rubrica(self, rubricas, codigo_rubrica):
        for rubrica in rubricas:
            if rubrica.code == codigo_rubrica:
                return rubrica.total
        return 0.00

    @api.multi
    def _buscar_codigo_outras_entidades(self):
        if fields.Date.from_string(self.ano+"-"+self.mes+"-01") < fields.Date.\
                from_string("1998-10-01"):
            return '    '
        if self.codigo_recolhimento in \
                ['115', '130', '135', '150', '155', '211', '608', '650']:
            return self.company_id.codigo_outras_entidades
        if self.codigo_recolhimento in \
                ['145', '307', '317', '327', '337', '345', '640', '660']:
            return self.company_id.codigo_outras_entidades
        if self.codigo_fpas == "582" and fields.Date.\
                from_string(self.mes+"-"+self.ano+"-01") >= fields.\
                Date.from_string("1999-04-01"):
            return '0000'
        if self.codigo_fpas == "639" and fields.Date.\
                from_string(self.mes+"-"+self.ano+"-01") < fields.Date.\
                from_string("1998-10-01"):
            return '    '
        if self.codigo_fpas == "868":
            return '0000'
        if self._simples(self.company_id) in ['1', '4', '5']:
            return self.company_id.codigo_outras_entidades
        if self._simples(self.company_id) in ['2', '3', '6']:
            return '    '

    @api.multi
    def _buscar_codigo_pagamento_gps(self):
        if fields.Date.from_string(self.ano + "-" + self.mes + "-01") <\
                fields.Date.from_string("1998-10-01"):
            return '    '
        if self.codigo_recolhimento in ['115', '150', '211', '650']:
            return self.company_id.codigo_recolhimento_GPS
        if self.codigo_fpas == "868":
            if self.company_id.codigo_recolhimento_GPS in ['1600', '1651']:
                return self.company_id.codigo_recolhimento_GPS
        return '    '

    @api.multi
    def _buscar_isencao_filantropia(self):
        if self.codigo_fpas == "639":
            return str("%05d" % self.porcentagem_filantropia*100)
        return '    '

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
    codigo_recolhimento_gps = fields.Integer(
        string=u'Código de recolhimento do GPS',
        related='company_id.codigo_recolhimento_GPS',
        store=True,
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
    codigo_outras_entidades = fields.Selection(
        string=u'Código de outras entidades',
        related='company_id.codigo_outras_entidades',
        store=True,
    )
    centralizadora = fields.Selection(
        selection=CENTRALIZADORA,
        string=u'Centralizadora',
        default='1',
        required=True,
        help="""Para indicar as empresas que centralizam o recolhimento do
         FGTS\n- Deve ser igual a zero (0), para os códigos de recolhimento
          130, 135, 150, 155, 211, 317, 337, 608 e para empregador doméstico
         (FPAS 868).\n- Quando existir empresa centralizadora deve existir,
         no mínimo, uma empresa centralizada e vice-versa.\n - Quando existir
          centralização, as oito primeiras posições\n do CNPJ da
          centralizadora e da centralizada devem ser iguais.\n- Empresa com
           inscrição CEI não possui centralização.\n"""
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
            return linha + '\r\n'
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

    def _rat(self, company):
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
            [('year', '=', self.ano),
            ('company_id', '=', company.id)
             ], limit=1).rat_rate or '0'

    def _simples(self, company_id):
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
        if company_id.fiscal_type == '3':
            return '1'
        else:
            return '2'

    def _tipo_inscricao_cnae(self, company_id):
        if company_id.partner_id.is_company:
            tipo_inscr_empresa = '1'
            inscr_empresa = company_id.cnpj_cpf
            cnae = company_id.cnae_main_id.code
        else:
            raise ValidationError(_(
                'Exportação de empregador doméstico não parametrizada '
                'corretamente'))
            tipo_inscr_empresa = '0'
            # TODO: Campo não implementado
            inscr_empresa = company_id.cei
            cnae = company_id.cnae
            if '9700500' not in cnae:
                raise ValidationError(_(
                    'Para empregador doméstico utilizar o número 9700500.'
                ))
        return tipo_inscr_empresa, inscr_empresa, cnae

    def _ded_13_lic_maternidade(self):
        """ Registro 12 item 5:

                    Dedução 13o Salário Licença
            Maternidade
            (Informar o valor da parcela de 13o salário referente ao período
            em que a trabalhadora esteve em licença maternidade, nos casos
            em que o empregador/contribuinte for responsável pelo pagamento do
            salário-maternidade.
            A informação deve ser prestada nas seguintes situações:
            - na competência 13, referente ao valor pago durante o ano.
            - na competência da rescisão do contrato de trabalho (exceto
            rescisão por justa causa), aposentadoria sem continuidade
            de vínculo ou falecimento )

            Opcional para a competência 13.
            Opcional para o código de recolhimento 115.
            Opcional para os códigos de recolhimento 150, 155 e 608, quando o
            CNPJ da empresa for igual ao CNPJ do tomador.
            Deve ser informado quando houver movimentação por rescisão de
            contrato de trabalho (exceto rescisão com justa causa),
            aposentadoria sem continuidade de vínculo, aposentadoria por
            invalidez ou falecimento, para empregada que possuir afastamento
            por motivo de licença maternidade no ano.
            Não pode ser informado para os códigos de recolhimento 130, 135,
            145, 211, 307, 317, 327, 337, 345, 640, 650, 660 e para empregador
            doméstico (FPAS 868).
            Não pode ser informado para licença maternidade iniciada a partir
            de 01/12/1999 e com benefícios requeridos até 31/08/2003.
            Não pode ser informado para competências anteriores a 10/1998.
            Não pode ser informado para as competências 01/2001 a 08/2003.
            Sempre que não informado preencher com zeros.

        :return:
        """
        if self.mes == '13':
            total = 0.00
            for ocorrencia in self.env['hr.holidays'].search([
                ('holiday_status_id.name', '=', 'Licença Maternidade'),
                ('data_inicio', '>=', self.ano + '-01-01'),
                ('data_fim', '<=', self.ano + '-12-31'),
            ]):
                total += (
                    ocorrencia.contrato_id.wage *
                    ocorrencia.number_of_days_temp / 30)
            return total
        else:
            rescisoes = self.env['hr.payslip'].search([
                ('mes_do_ano', '=', self.mes),
                ('ano', '=', self.ano),
                ('tipo_de_folha', '=', 'rescisao')
            ])
            total = 0.00
            for rescisao in rescisoes:
                for ocorrencia in self.env['hr.holidays'].search([
                    ('contrato_id.id', '=', rescisao.contract_id.id),
                    ('holiday_status_id.name', '=', 'Licença Maternidade'),
                    ('data_inicio', '>=', self.ano + '-01-01'),
                    ('data_fim', '<=', self.ano + '-' + self.mes + '-31'),
                ]):
                    total += (ocorrencia.contrato_id.wage *
                              ocorrencia.number_of_days_temp / 30)
            return total

    def _get_folha_ids(self):
        raiz = self.company_id.cnpj_cpf.split('/')[0]
        folha_ids = self.env['hr.payslip'].search([
            ('mes_do_ano', '=', self.mes),
            ('ano', '=', self.ano),
            ('state', '=', 'done'),
            ('company_id.partner_id.cnpj_cpf', 'like', raiz)
        ])
        return folha_ids

    @api.multi
    def gerar_sefip(self):
        for record in self:
            sefip = SEFIP()
            record.sefip = ''
            record.sefip += \
                self._valida_tamanho_linha(
                    record._preencher_registro_00(sefip))

            folha_ids = record._get_folha_ids()

            for company_id in folha_ids.mapped('company_id'):
                folhas_da_empresa = folha_ids.filtered(
                    lambda r: r.company_id == company_id)

                record.sefip += self._valida_tamanho_linha(
                    self._preencher_registro_10(company_id, sefip))
                for folha in folhas_da_empresa.sorted(
                        key=lambda folha: punctuation_rm(
                            folha.employee_id.pis_pasep)):
                    record.sefip += self._valida_tamanho_linha(
                        record._preencher_registro_30(sefip, folha))

                    if folha.tipo_de_folha == 'rescisao':
                        record.sefip += self._valida_tamanho_linha(
                            record._preencher_registro_32(sefip, folha))

            record.sefip += sefip._registro_90_totalizador_do_arquivo()

            # Cria um arquivo temporario txt e escreve o que foi gerado
            path_arquivo = sefip._gerar_arquivo_temp(self.sefip, 'SEFIP')
            # Gera o anexo apartir do txt do grrf no temp do sistema
            mes = str(self.mes) if self.mes > 9 else '0' + str(self.mes)
            nome_arquivo = 'SEFIP.re'
            self._gerar_anexo(nome_arquivo, path_arquivo)

    def _preencher_registro_00(self, sefip):
        sefip.tipo_inscr_resp = '1' if \
            self.responsible_user_id.parent_id.is_company else '3'
        sefip.inscr_resp = self.responsible_user_id.parent_id.cnpj_cpf
        sefip.nome_resp = self.responsible_user_id.parent_id.legal_name
        sefip.nome_contato = (self.responsible_user_id.legal_name or
                              self.responsible_user_id.name)
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
            if self.data_recolhimento_gps else ''
        sefip.tipo_inscr_fornec = (
            '1' if self.company_id.supplier_partner_id.is_company else '3')
        sefip.inscr_fornec = self.company_id.supplier_partner_id.cnpj_cpf
        return sefip._registro_00_informacoes_responsavel()

    def _preencher_registro_10(self, company_id, sefip):

        tipo_inscr_empresa, inscr_empresa, cnae = self._tipo_inscricao_cnae(
            company_id
        )

        sefip.tipo_inscr_empresa = tipo_inscr_empresa
        sefip.inscr_empresa = inscr_empresa
        sefip.emp_nome_razao_social = (
            company_id.legal_name or company_id.name or ''
        )
        logadouro, bairro, cep, cidade, uf, telefone = \
            self._logadouro_bairro_cep_cidade_uf_telefone(
                'da empresa', company_id.partner_id
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
        sefip.emp_aliquota_RAT = self._rat(company_id)
        sefip.emp_cod_centralizacao = self.centralizadora
        sefip.emp_simples = self._simples(company_id)
        sefip.emp_FPAS = self.codigo_fpas
        sefip.emp_cod_outras_entidades = self._buscar_codigo_outras_entidades()
        sefip.emp_cod_pagamento_GPS = self._buscar_codigo_pagamento_gps()
        sefip.emp_percent_isencao_filantropia = \
            self._buscar_isencao_filantropia()
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

    def _trabalhador_remun_sem_13(self, folha):
        """ Registro 30. Item 16

        Rubrica Base do INSS

        """
        result = 0.00
        #
        # Não pode ser informado para a competência 13
        #
        if folha.tipo_de_folha == 'decimo_terceiro':
            return result
        # #
        # # As remunerações pagas após rescisão do contrato de trabalho e
        # # conforme determinação do Art. 466 da CLT,
        # # não devem vir acompanhadas das respectivas movimentações.
        # #
        # elif False:
        #     # TODO:
        #     result = 0.00

        # #
        # # Obrigatório
        # #
        # elif folha.contract_id.categoria_sefip in (
        #         '05', '11', '13', '14', '15', '16', '17', '18', '22', '23',
        #         '24', '25'):
        #     result = folha.base_inss
        # #
        # # Opcional
        # #
        # elif folha.contract_id.categoria_sefip in (
        #         '01', '02', '03', '04', '06', '07', '12', '19', '20', '21',
        #         '26'):
        #     result = folha.base_inss

        result = self._retornar_valor_rubrica(folha.line_ids, "BASE_INSS")
        result += self._retornar_valor_rubrica(
            folha.line_ids, "BASE_INSS_FERIAS")
        return result

    def _trabalhador_remun_13(self, folha):
        """ Registro 30. Item 17

        Rúbrica 13 Base do INSS (Somente na rescisão temos o 16 e o 17!)

        """
        result = 0.00
        #
        # Não pode ser informado para a competência 13
        #
        if folha.tipo_de_folha == 'rescisao':
            return result

        # #
        # # As remunerações pagas após rescisão do contrato de trabalho e
        # # conforme determinação do Art. 466 da CLT,
        # # não devem vir acompanhadas das respectivas movimentações .
        # #
        # elif False:
        #     # TODO:
        #     result = 0.00
        # #
        # # Campo obrigatório para categoria 02.
        # #
        # elif folha.contract_id.categoria_sefip == '02':
        #     # TODO: Implementar campo para calcular a rúbrica do 13 do INSS
        #     # BASE_INSS_13
        #     # ou pesquisar manualemnte
        #     result = 0.00
        # elif folha.contract_id.categoria_sefip in (
        #         '01', '03', '04', '06', '07', '12', '19', '20', '21', '26'):
        #     # TODO:
        #     result = 0.00
        # return result

        return self._retornar_valor_rubrica(
            folha.line_ids, 'ADIANTAMENTO_13_FERIAS')

    def _trabalhador_classe_contrib(self, folha):
        """ Registro 30. Item 18
        Classe de Contribuição (Indicar a classe de contribuição do autônomo,
        quando a empresa opta por contribuir sobre seu salário-base e os
        classifica como categoria 14 ou 16. A classe deve estar compreendida
        em tabela fornecida pelo INSS). """

        result = '  '
        # #
        # # Não pode ser informado para a competência 13
        # #
        # if folha.tipo_de_folha == 'decimo_terceiro':
        #     return result
        # #
        # # Campo obrigatório para as categorias 14 e 16
        # # (apenas em recolhimentos de competências anteriores a 03/2000).
        # #
        # elif (fields.Date.from_string(folha.date_from) <
        #       fields.Date.from_string('2000-03-01') and
        #       folha.contract_id.categoria_sefip in ('14', '16')):
        #     # TODO:
        #     return 0.00
        return result

    def _buscar_multiplos_vinculos(self, folha):
        """ Esta informação deve ser lançada manualmente no payslip

        :param folha:
        :return:
        """
        #TODO: Implementar no payslip
        return []


    def _buscar_ocorrencias(self, folha):
        """ Estas informações devem ser lançadas na folha

        :param folha:
        :return:
        """
        # FIXME: Deste jeito não deu certo, pois existem afastamentos s/ data

        return []

        folha_date_from = fields.Date.from_string(folha.date_from)
        folha_date_to = fields.Date.from_string(folha.date_to)

        ocorrencia_aprovada_ids = folha.contract_id.afastamento_ids.filtered(
            lambda r: r.state == 'validate')
        ocorrencias_no_periodo_ids = ocorrencia_aprovada_ids.filtered(
            lambda r: (folha_date_from >=
                       fields.Date.from_string(r.data_inicio) and
                       fields.Date.from_string(r.data_fim) <= folha_date_to))

        return ocorrencias_no_periodo_ids

    def _trabalhador_ocorrencia(self, folha):
        """ Registro 30. Item 19
        Ocorrencia: Acidente de trabalho, rescisão, afastamento por
        doença lic maternidade, ( situaçeõs que o funcionario deixa de
        trablalhar e o inss deverá assumir o pagamento do funcionário)

        Nao implementado:

         - Para empregado doméstico (Cat 06) e diretor não empregado
         (Cat 05) permitido apenas branco ou 05.
         -

        """
        folha_ids = self._get_folha_ids()
        count = 0
        for folha_id in folha_ids:
            if folha.employee_id.id == folha_id.employee_id.id:
                count += 1
        if count == 2:
            return '05'
        ocorrencia = ' '
        permitido = False

        # TODO:
        if folha.tipo_de_folha == 'rescisao':
            # FIXME:
            # return hr.payroll.structure.tipo_afastamento_sefip
            print ("tipo_afastamento_sefip - Registro 30. Item 19")
            pass

        ocorrencias_no_periodo_ids = self._buscar_ocorrencias(folha)

        if not ocorrencias_no_periodo_ids:
            return ocorrencia

        # Vai o código do afastamento mais longo e é sempre informado
        # A lógica abaixo pode ser removida

        # #
        # # Obrigatório para categoria 26,
        # # devendo ser informado 05, 06, 07 ou 08.
        # #
        # if folha.contract_id.categoria_sefip == '26':
        #     permitido = ['05', '06', '07', '08']
        #     # TODO:
        #     ocorrencia = '05'
        # elif folha.contract_id.categoria_sefip in (
        #         '02', '22', '23'
        # ):
        #     permitido = [' ', '01', '02', '03', '04']
        #
        # if permitido and ocorrencia in permitido:
        #     return ocorrencia
        # elif permitido and ocorrencia not in permitido:
        #     raise ValidationError(
        #         _("A ocorrência {0} não é permitida para folha de pagamento"
        #           " de \n {1}, referente a {2}."
        #             .format(
        #                 OCORRENCIA_SEFIP[ocorrencia],
        #                 folha.contract_id.name,
        #                 folha.data_extenso
        #             )))
        # return ocorrencia

    def _trabalhador_valor_desc_segurado(self, folha):
        """ Registro 30. Item 20.

        Valor Descontado do Segurado (Destinado à informação do valor da
        contribuição do trabalhador com mais de um vínculo empregatício;
        ou quando tratar-se de recolhimento de trabalhador avulso,
        dissídio coletivo ou reclamatória trabalhista, ou, ainda nos meses
        de afastamento e retorno de licença maternidade)
        O valor informado será considerado como contribuição do segurado.

        --
        Verificar se no cliente, por exemplo,
        o funcionário esta contratado em 2 lugares pois o INSS recolhido
        em outro lugar pode ter que ser informado aqui.

        """
        result = 0

        if (fields.Date.from_string(folha.date_from) <
                fields.Date.from_string('1998-10-01')):
            return result
        #
        # Campo opcional para os códigos de recolhimento 130, 135 e 650.
        #
        if self.codigo_recolhimento in ('130', '135', '650'):
            return 0

        multiplos_vinculos_ids = self._buscar_multiplos_vinculos(folha)

        if not multiplos_vinculos_ids:
            return 0.00

            # TODO:
            # Campo opcional para as ocorrências 05, 06, 07 e 08.
            # Campo opcional para as categorias de trabalhadores igual a
            # 01, 02, 04, 06, 07, 12, 19, 20, 21 e 26.
            # Campo opcional para as categorias de trabalhadores igual a
            # 05, 11, 13, 15, 17, 18, 24 e 25 a partir da competência 04/2003.

        return 0.00

    def _trabalhador_remun_base_calc_contribuicao_previdenciaria(self, folha):
        """ Registro 30. Item 21

        Remuneração base de cálculo da contribuição previdenciária
        (Destinado à informação da parcela de remuneração sobre a qual incide
        contribuição previdenciária, quando o trabalhador estiver afastado
        por motivo de acidente de trabalho e/ou prestação de serviço
        militar obrigatório ou na informação de Recolhimento
        Complementar de FGTS)


        Preenchido somente quando o funcionário esta afastado.

        Geralmente Zerado

        """
        return 0.00

    def _trabalhador_base_calc_13_previdencia_competencia(self, folha):
        """ Registro 30. Item 22

        Base de Cálculo 13 Salário Previdência Social –
        Referente à competência do movimento

        (Na competência em que ocorreu o afastamento definitivo – informar o
        valor total do 13o pago no ano ao trabalhador.
        Na competência 12 – Indicar eventuais diferenças de gratificação
        natalina de empregados que recebem remuneração variável – Art. 216,
        Parágrafo 25, Decreto 3.265 de 29.11.1999)

        Na competência 13, para a geração da GPS, indicar o valor total do
        13o salário pago no ano ao trabalhador)

        """

        if folha.tipo_de_folha == 'rescisao':
            return self._retornar_valor_rubrica(folha.line_ids, "BASE_INSS_13")
        return 0.00

    def _trabalhador_base_calc_13_previdencia_GPS(self, folha):
        """ Registro 30. Item 23

        Base de Cálculo 13 Salário Previdência – Referente
        à GPS da competência 13.

        Deve ser utilizado apenas na competência 12, informando o valor
        da base de cálculo do 13o dos empregados que recebem remuneração
        variável, em relação a remuneração apurada até 20/12 sobre
        a qual já houve recolhimento em GPS ).

        """
        if folha.tipo_de_folha == 'decimo_terceiro':
            return folha.base_inss
        return 0.00

    def _preencher_registro_30(self, sefip, folha):
        """

        Recomendações gerais!:

        Uma linha para cada folha do periodo, sendo rescisão, normal.
        Férias não entra.
        Na competência 13 considerar somente o 13.

        """
        # if folha.tipo_de_folha == 'ferias':

        codigo_categoria = folha.contract_id.categoria_sefip

        tipo_inscr_empresa, inscr_empresa, cnae = self._tipo_inscricao_cnae(
            folha.company_id
        )
        sefip.tipo_inscr_empresa = tipo_inscr_empresa
        sefip.inscr_empresa = inscr_empresa

        if self.codigo_recolhimento in (
                '130', '135', '211', '150', '155', '317', '337', '608'):
            sefip.tipo_inscr_tomador = ' '
            sefip.inscr_tomador = ' ' * 14

        sefip.pis_pasep_ci = folha.employee_id.pis_pasep

        if codigo_categoria in ('01', '03', '04', '05', '06', '07', '11',
                                '12', '19', '20', '21', '26'):
            sefip.data_admissao = fields.Datetime.from_string(
                folha.contract_id.date_start).strftime('%d%m%Y')

        if codigo_categoria in ('01', '03', '04', '05', '06', '07', '11',
                                '12', '19', '20', '21'):
            sefip.categoria_trabalhador = codigo_categoria

        sefip.nome_trabalhador = folha.employee_id.name

        if codigo_categoria not in (
                '06', '13', '14', '15', '16', '17', '18', '22', '23',
                '24', '25'):
            sefip.matricula_trabalhador = folha.employee_id.registration

        if codigo_categoria in ('01', '03', '04', '06', '07', '26'):
            sefip.num_ctps = folha.employee_id.ctps
            sefip.serie_ctps = folha.employee_id.ctps_series

        if codigo_categoria in ('01', '03', '04', '05', '06', '07'):
            # Item 13: Data de opção do FGtS, é sempre a data de contratação!
            sefip.data_de_opcao = fields.Datetime.from_string(
                folha.contract_id.date_start).strftime('%d%m%Y')
        else:
            sefip.data_de_opcao = '      '

        if codigo_categoria in ('01', '02', '03', '04', '05', '06', '07',
                                '12', '19', '20', '21', '26'):
            sefip.data_de_nascimento = fields.Datetime.from_string(
                folha.employee_id.birthday).strftime('%d%m%Y')
        else:
            sefip.data_de_nascimento = '      '

        if codigo_categoria in '06':
            sefip.trabalhador_cbo = '05121'
        else:
            sefip.trabalhador_cbo = '0' + \
                                    folha.contract_id.job_id.cbo_id.code[:4]
        # Revisar daqui para a frente
        sefip.trabalhador_remun_sem_13 = \
            self._trabalhador_remun_sem_13(folha)

        sefip.trabalhador_remun_13 = self._trabalhador_remun_13(folha)

        sefip.trabalhador_classe_contrib = \
            self._trabalhador_classe_contrib(folha)

        sefip.trabalhador_ocorrencia = self._trabalhador_ocorrencia(folha)
        sefip.trabalhador_valor_desc_segurado = \
            self._trabalhador_valor_desc_segurado(folha)
        sefip.trabalhador_remun_base_calc_contribuicao_previdenciaria = \
            self._trabalhador_remun_base_calc_contribuicao_previdenciaria(
                folha)
        sefip.trabalhador_base_calc_13_previdencia_competencia = \
            self._trabalhador_base_calc_13_previdencia_competencia(folha)
        sefip.trabalhador_base_calc_13_previdencia_GPS = \
            self._trabalhador_base_calc_13_previdencia_GPS(folha)

        return sefip._registro_30_registro_do_trabalhador()

    def _preencher_registro_32(self, sefip, folha):
        """

        Registro de movimentação de Trabalhador

        """
        tipo_afastamento = folha.struct_id.tipo_afastamento_sefip
        sefip.trabalhador_codigo_movimentacao = tipo_afastamento or ''
        sefip.trabalhador_data_movimentacao = folha.data_afastamento or ''
        # No exemplo de SEFIP da ABGF todos os registros 32 tem o seguinte
        # campo em branco
        sefip.trabalhador_indic_recolhimento_fgts = ' '

        return sefip._registro_32_movimentacao_do_trabalhador()

    def _gerar_anexo(self, nome_do_arquivo, path_arquivo_temp):
        """
        Função gerar anexo dentro do SEFIP, sobrescrevendo anexo existente.
         Apartir de um arquivo temporário. Deve ser passado o path do
         arquivo temporário que se tornará anexo da sefip
        :param nome_do_arquivo:
        :param path_arquivo_temp:
        :return:
        """
        attachment_obj = self.env['ir.attachment']

        # Apagar SEFIP's existentes
        anexos = attachment_obj.search([('res_id', '=', self.id)])
        for anexo in anexos:
            anexo.unlink()

        try:
            file_attc = open(path_arquivo_temp, 'r')
            attc = file_attc.read()

            attachment_data = {
                'name': nome_do_arquivo,
                'datas_fname': nome_do_arquivo,
                'datas': base64.b64encode(attc),
                'res_model': 'l10n_br.hr.sefip',
                'res_id': self.id,
            }
            attachment_obj.create(attachment_data)
            file_attc.close()

        except:
            raise Warning(
                _('Impossível gerar Anexo do %s' % nome_do_arquivo))
