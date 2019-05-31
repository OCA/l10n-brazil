# -*- coding: utf-8 -*-
# (c) 2017 KMEE INFORMATICA LTDA - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# (c) 2017 KMEE INFORMATICA LTDA - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import (
    division, print_function, unicode_literals, absolute_import
)

import os
import tempfile
import logging
import base64
import pybrasil
from py3o.template import Template
from datetime import timedelta
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
from pybrasil.valor import formata_valor
from pybrasil.data import formata_data
import subprocess
import calendar

from openerp.addons.l10n_br_base.tools.misc import punctuation_rm

from .arquivo_sefip import SEFIP
from ..constantes_rh import (
    MESES,
    MODALIDADE_ARQUIVO,
    CODIGO_RECOLHIMENTO,
    RECOLHIMENTO_GPS,
    RECOLHIMENTO_FGTS,
)

_logger = logging.getLogger(__name__)
CURDIR = os.path.dirname(os.path.abspath(__file__))


class SefipAttachments(models.Model):
    _name = b'l10n_br.hr.sefip.attachments'
    _order = b'create_date'

    name = fields.Char(string='Observações')
    type = fields.Selection(string='Tipo', selection=[
        ('sent', 'Enviado'),
        ('relatorio', 'relatorio'),
    ], default='relatorio')
    sefip_id = fields.Many2one(
        string='Arquivo do governo relacionado',
        comodel_name=b'l10n_br.hr.sefip'
    )
    attachment_ids = fields.Many2many(
        string='Arquivo anexo',
        comodel_name='ir.attachment',
        relation='ir_attachment_sefip_rel',
        column1='sefip_attachment_id',
        column2='attachment_id',
    )


class L10nBrSefip(models.Model):
    _name = b'l10n_br.hr.sefip'
    _inherit = [b'abstract.arquivos.governo.workflow', b'mail.thread']

    @api.multi
    @api.onchange('company_id')
    def onchange_company_id(self):
        for sefip in self:
            if sefip.responsible_user_id:
                if sefip.responsible_user_id.parent_id != \
                        sefip.company_id.partner_id:
                    sefip.responsible_user_id = False
            return {
                'domain': {
                    'responsible_user_id':
                        [('parent_id', '=', sefip.company_id.partner_id.id)]
                }
            }

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
    def _valor_rubrica(self, rubricas, codigo_rubrica):
        for rubrica in rubricas:
            if rubrica.code == codigo_rubrica:
                return rubrica.total
        return 0.00

    @api.multi
    def _buscar_codigo_outras_entidades(self):

        # Se adaptar com o 13 salario onde mes == '13'. A variavel sera set 12
        mes = self.mes if self.mes <= '12' else '12'

        if (fields.Date.from_string(self.ano + "-" + mes + "-01") <
                fields.Date.from_string("1998-10-01")):
            return '    '
        if self.codigo_recolhimento in \
                ['115', '130', '135', '150', '155', '211', '608', '650']:
            return self.company_id.codigo_outras_entidades
        if self.codigo_recolhimento in \
                ['145', '307', '317', '327', '337', '345', '640', '660']:
            return self.company_id.codigo_outras_entidades
        if self.codigo_fpas == "582" and fields.Date.\
                from_string(mes + "-" + self.ano + "-01") >= fields.\
                Date.from_string("1999-04-01"):
            return '0000'
        if self.codigo_fpas == "639" and fields.Date.\
                from_string(mes + "-" + self.ano + "-01") < fields.Date.\
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

        # Se adaptar com o 13 salario onde mes == '13'. A variavel sera set 12
        mes = self.mes if self.mes <= '12' else '12'

        if fields.Date.from_string(self.ano + "-" + mes + "-01") <\
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
            return str("%05d" % self.porcentagem_filantropia * 100)
        return '    '

    related_attachment_ids = fields.One2many(
        string='Anexos Relacionados',
        comodel_name='l10n_br.hr.sefip.attachments',
        inverse_name='sefip_id',
        readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)], 'open': [('readonly', False)]}
    )
    responsible_user_id = fields.Many2one(
        comodel_name='res.partner', string=u'Usuário Responsável',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    company_id = fields.Many2one(
        comodel_name='res.company', string=u'Empresa',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    mes = fields.Selection(
        selection=MESES, string=u'Mês',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    ano = fields.Char(
        string=u'Ano', size=4,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    modalidade_arquivo = fields.Selection(
        selection=MODALIDADE_ARQUIVO, string=u'Modalidade do arquivo',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help= '• Pode ser:'
              '\nBranco – Recolhimento ao FGTS e Declaração à Previdência'
              '\n1 - Declaração ao FGTS e à Previdência'
              '\n9 - Confirmação Informações anteriores – Rec/Decl ao FGTS e Decl à Previdência'
              '\n • Para competência anterior a 10/1998 deve ser igual a branco ou 1.'
              '\n • A modalidade 9 não pode ser informada para competências anteriores a 10/1998.'
              '\n • Para os códigos 145, 307, 317, 327, 337, 345 e 640 deve ser igual a branco.'
              '\n • Para o código 211 deve ser igual a 1 ou 9.'
              '\n • Para o FPAS 868 deve igual a branco ou 9.'
              '\n • Para a competência 13, deve ser igual a 1 ou 9.'
              '\n • Serão acatadas até três cargas consecutivas de SEFIP.RE.'
              '\n • Deverá existir apenas um arquivo SEFIP.RE para cada modalidade.',
    )
    codigo_recolhimento = fields.Selection(
        string=u'Código de recolhimento', selection=CODIGO_RECOLHIMENTO,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    recolhimento_fgts = fields.Selection(
        string=u'Recolhimento do FGTS', selection=RECOLHIMENTO_FGTS,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    data_recolhimento_fgts = fields.Date(
        string=u'Data de recolhimento do FGTS',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    codigo_recolhimento_gps = fields.Integer(
        string=u'Código de recolhimento do GPS',
        related='company_id.codigo_recolhimento_GPS',
        store=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    recolhimento_gps = fields.Selection(
        string=u'Recolhimento do GPS', selection=RECOLHIMENTO_GPS,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    data_recolhimento_gps = fields.Date(
        string=u'Data de recolhimento do GPS',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    codigo_fpas = fields.Char(
        string=u'Código FPAS',
        default='736',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
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
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    codigo_outras_entidades = fields.Selection(
        string=u'Código de outras entidades',
        related='company_id.codigo_outras_entidades',
        store=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    eh_obrigatorio_informacoes_processo = fields.Boolean(
        compute='_compute_eh_obrigatorio_informacoes_processo',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    data_geracao = fields.Date(
        string=u'Data do arquivo',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    # Processo ou convenção coletiva
    num_processo = fields.Char(
        string=u'Número do processo',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    ano_processo = fields.Char(
        string=u'Ano do processo', size=4,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    vara_jcj = fields.Char(
        string=u'Vara/JCJ',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    data_inicio = fields.Date(
        string=u'Data de Início',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    data_termino = fields.Date(
        string=u'Data de término',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    sefip = fields.Text(
        string=u'Prévia do SEFIP',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    data_vencimento_grcsu = fields.Date(
        string=u'Data de Vencimento da GRCSU',
    )

    folha_ids = fields.One2many(
        string='Holerites',
        comodel_name='hr.payslip',
        inverse_name='sefip_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    folha_autonomo_ids = fields.One2many(
        string='Holerites de Autônomos',
        comodel_name='hr.payslip.autonomo',
        inverse_name='sefip_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    boletos_ids = fields.One2many(
        string='Guias/Boletos',
        comodel_name='financial.move',
        inverse_name='sefip_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    @api.onchange('company_id', 'ano', 'mes')
    def _onchange_data_vencimento_grcsu(self):
        self.ensure_one()
        if not (self.ano and self.mes and self.company_id):
            return

        mes = self.mes if self.mes < '13' else '12'
        ultimo_dia_mes = str(self.ano) + '-' + mes + '-01'
        ultimo_dia_mes = pybrasil.data.mes_que_vem(ultimo_dia_mes)
        ultimo_dia_mes = pybrasil.data.ultimo_dia_mes(ultimo_dia_mes)
        estado = self.company_id.state_id.code
        municipio = self.company_id.l10n_br_city_id.name
        self.data_vencimento_grcsu = pybrasil.data.dia_util_pagamento(
                ultimo_dia_mes,
                estado=estado,
                municipio=municipio,
                antecipa=True
        )

        # segundo o leiaute do SEFIP para competencia 13 esse campo deverá ser
        # igual a 1 ou 9.
        if self.mes == '13':
            self.modalidade_arquivo = '1'
            self.recolhimento_fgts = ' '

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
        # if not partner_id.number:
        #     erro += _("Número {0} não preenchido\n".format(type))
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
                ultimo_dia_mes = calendar.monthrange(int(self.ano), int(self.mes))[1]
                for ocorrencia in self.env['hr.holidays'].search([
                    ('contrato_id.id', '=', rescisao.contract_id.id),
                    ('holiday_status_id.name', '=', 'Licença Maternidade'),
                    ('data_inicio', '>=', self.ano + '-01-01'),
                    ('data_fim', '<=', self.ano + '-' + self.mes + '-' +
                        str(ultimo_dia_mes)),
                ]):
                    total += (ocorrencia.contrato_id.wage *
                              ocorrencia.number_of_days_temp / 30)
            return total

    def _get_folha_autonomos_ids(self):
        """
        Buscar os holerites de autonomos que irao compor o SEFIP do mes
        :return:
        """
        mes_do_ano = self.mes
        tipo_de_folha = ['normal']

        # No caso do demonstrativo de decimo terceiro
        if mes_do_ano == '13':
            # Monta data para algumas vericacoes, logo deve setar
            tipo_de_folha = ['decimo_terceiro']

        raiz = self.company_id.cnpj_cpf.split('/')[0]
        folha_autonomo_ids = self.env['hr.payslip.autonomo'].search([
            ('mes_do_ano', '=', mes_do_ano),
            ('ano', '=', self.ano),
            ('tipo_de_folha', 'in', tipo_de_folha),
            ('state', 'in', ['done','verify']),
            ('company_id.partner_id.cnpj_cpf', 'like', raiz),
        ]).filtered('total_folha')
        # Filtered eh para pegar apenas os holerites que nao estao zerados

        return folha_autonomo_ids

    def _get_folha_ids(self):
        """
        Buscar os holerites que irao compor o SEFIP do mes
        :return:
        """
        mes_do_ano = self.mes
        tipo_de_folha = ['normal', 'rescisao', 'rescisao_complementar']

        # No caso do demonstrativo de decimo terceiro
        if mes_do_ano == '13':
            # Monta data para algumas vericacoes, logo deve setar
            tipo_de_folha = ['decimo_terceiro']

        raiz = self.company_id.cnpj_cpf.split('/')[0]
        folha_ids = self.env['hr.payslip'].search([
            ('mes_do_ano', '=', mes_do_ano),
            ('ano', '=', self.ano),
            ('tipo_de_folha', 'in', tipo_de_folha),
            ('state', 'in', ['done','verify']),
            ('company_id.partner_id.cnpj_cpf', 'like', raiz),
            ('contract_id.gerar_sefip', '=', True),
        ]).filtered('total_folha')
        # Filtered eh para pegar apenas os holerites que nao estao zerados

        return folha_ids

    def _valida_centralizadora(self, companies):
        options = []
        for company in companies:
            options.append(company.centralizadora)
        if '1' in options:
            if '2' not in options:
                raise ValidationError(
                    _(u'Existe uma empresa centralizadora porém não '
                      u'existe nenhuma centralizada')
                )
        if '2' in options:
            if '1' not in options:
                raise ValidationError(
                    _(u'Existe uma empresa centralizada porém não '
                      u'existe nenhuma centralizadora')
                )

    @api.multi
    def criar_anexo_sefip(self):
        sefip = SEFIP()
        for record in self:
            # Cria um arquivo temporario txt e escreve o que foi gerado
            path_arquivo = sefip._gerar_arquivo_temp(record.sefip, 'SEFIP')
            # Gera o anexo apartir do txt do grrf no temp do sistema
            nome_arquivo = 'SEFIP.re'
            self._gerar_anexo(nome_arquivo, path_arquivo)

    def valida_anexos(self):
        tipos_anexo = [x.type for x in self.related_attachment_ids]
        if 'sent'in tipos_anexo and 'relatorio' in tipos_anexo:
            return True
        else:
            raise ValidationError(
                _('É necessário adicionar o relatório gerado pelo '
                  'aplicativo na aba "Arquivos Anexos" para confirmar o envio')
            )

    def prepara_financial_move(self, partner_id, sindicato_info):
        '''
         Tratar dados do sefip e criar um dict para criar financial.move de 
         contribuição sindical.
        :param partner_id: id do partner do sindicato 
        :param valor:  float com valor total de contribuição
        :return: dict com valores para criar financial.move
        '''

        sequence_id = \
            self.company_id.payment_mode_sindicato_id.sequence_arquivo_id.id
        doc_number = str(self.env['ir.sequence'].next_by_id(sequence_id))

        # Total de contratos ativos na empresa
        total_contratos = self.env['hr.contract'].search([
            '&',
            ('company_id', '=', self.company_id.id),
            '|',
            ('date_end', '>', fields.Date.today()),
            ('date_end', '=', False),
        ])
        # Filtrar contratos por usuarios
        total_funcionarios = len(total_contratos.mapped('employee_id'))

        return {
            'date_document': fields.Date.today(),
            'partner_id': partner_id,
            'doc_source_id': 'l10n_br.hr.sefip,' + str(self.id),
            'company_id': self.company_id.id,
            'amount_document': sindicato_info.get('contribuicao_sindicato'),
            'document_number': doc_number,
            'account_id': self.company_id.financial_account_sindicato_id.id,
            'document_type_id': self.company_id.document_type_sindicato_id.id,
            'payment_mode_id': self.company_id.payment_mode_sindicato_id.id,
            'type': '2pay',
            'sindicato_total_remuneracao_contribuintes':
                sindicato_info.get('total_remuneracao'),
            'sindicato_qtd_contribuintes':
                sindicato_info.get('qtd_contribuintes'),
            'sindicato_total_empregados': total_funcionarios,
            'date_maturity': self.data_vencimento_grcsu,
            'sefip_id': self.id,
        }

    def gerar_financial_move_darf(
            self, codigo_receita, valor, partner_id=False):
        '''
         Tratar dados do sefip e criar um dict para criar financial.move de
         guia DARF.
        :param DARF:  float com valor total do recolhimento
        :return: dict com valores para criar financial.move
        '''

        # Número do documento da DARF
        sequence_id = self.company_id.darf_sequence_id.id
        doc_number = str(self.env['ir.sequence'].next_by_id(sequence_id))
        num_referencia = ''

        # Definir quem sera o contribuinte da DARF, se nao passar nenhum
        # nos parametros assume que é a empresa
        if not partner_id:
            partner_id = self.company_id.partner_id

        # Preencher campo para indicar tipo de financial.move e tambem
        # preencher a data de vencimento
        descricao = 'DARF'

        if codigo_receita == '0588':
            descricao += ' - Diretores'

        if codigo_receita == '0561':
            descricao += ' - Funcionários'

        if codigo_receita == '1661':
            descricao += ' - PSS Plano de Seguridade Social'
            num_referencia = partner_id.cnpj_cpf

        if codigo_receita == '1850':
            num_referencia = self.company_id.partner_id.cnpj_cpf
            descricao += ' - PSS Patronal'

        # Calcular data de vencimento da DARF
        # data de vencimento setada na conf da empresa
        dia = str(self.company_id.darf_dia_vencimento)

        # ou se forem darfs especificas, cair no dia 05 de cada mes
        if codigo_receita in ['1850', '1661']:
            dia = '07'

        data = self.ano + '-' + self.mes + '-' + dia
        data_vencimento = \
            fields.Datetime.from_string(data + ' 03:00:00') + timedelta(days=31)

        # Antecipar data caso caia em feriado
        while not self.company_id.default_resource_calendar_id.\
                data_eh_dia_util(data_vencimento):
            data_vencimento -= timedelta(days=1)

        # Gerar FINANCEIRO da DARF
        vals_darf = {
            'date_document': fields.Date.today(),
            'partner_id': partner_id.id,
            'doc_source_id': 'l10n_br.hr.sefip,' + str(self.id),
            'company_id': self.company_id.id,
            'amount_document': valor,
            'document_number': 'DARF-' + str(doc_number),
            'account_id': self.company_id.darf_account_id.id,
            'document_type_id': self.company_id.darf_document_type.id,
            'type': '2pay',
            'date_maturity': data_vencimento,
            'payment_mode_id': self.company_id.darf_carteira_cobranca.id,
            'sefip_id': self.id,
            'cod_receita': codigo_receita,
            'descricao': descricao,
            'num_referencia': num_referencia,
        }
        financial_move_darf = self.env['financial.move'].create(vals_darf)

        # Gerar PDF da DARF
        financial_move_darf.button_boleto()

        return financial_move_darf

    def gerar_financial_move_gps(self, empresa_id, dados_empresa):
        '''
         Criar financial.move de guia GPS, imprimir GPS e anexá-la ao move.
        :param GPS: float com valor total do recolhimento
        :return: financial.move
        '''

        empresa = self.env['res.company'].browse(empresa_id)

        sequence_id = empresa.darf_sequence_id.id
        doc_number = str(self.env['ir.sequence'].next_by_id(sequence_id))

        GPS = dados_empresa['INSS_funcionarios'] + \
              dados_empresa['INSS_empresa'] + \
              dados_empresa['INSS_outras_entidades'] + \
              dados_empresa['INSS_rat_fap']

        INSS = dados_empresa['INSS_funcionarios'] + \
               dados_empresa['INSS_empresa'] + \
               dados_empresa['INSS_rat_fap']

        TERCEIROS = dados_empresa['INSS_outras_entidades']

        descricao = 'GPS - '+ empresa.name

        # Gerar movimentação financeira do GPS
        vals_gps = {
            'date_document': fields.Date.today(),
            'partner_id': self.env.ref('base.user_root').id,
            'doc_source_id': 'l10n_br.hr.sefip,' + str(self.id),
            'company_id': empresa_id,
            'document_number': 'GPS-' + str(doc_number),
            'account_id': empresa.gps_account_id.id,
            'document_type_id': empresa.gps_document_type.id,
            'type': '2pay',
            'date_maturity': self.data_recolhimento_gps,
            'payment_mode_id': empresa.gps_carteira_cobranca.id,
            'sefip_id': self.id,
            'valor_inss_terceiros': str(TERCEIROS),
            'valor_inss': str(INSS),
            'amount_document': GPS,
            'descricao': descricao,
        }
        financial_move_gps = self.env['financial.move'].create(vals_gps)

        # Gerar PDF DA GPS
        financial_move_gps.button_boleto()

        return financial_move_gps

    def buscar_IRPF_holerite_13(self, contrato):
        """
        Buscar o valor do IRPF do holerite de 13º
        :param contrato:
        :return:
        """
        holerite = self.env['hr.payslip'].search([
            ('contract_id', '=', contrato.id),
            ('mes_do_ano', '=', '13'),
            ('ano', '=', self.ano),
            ('tipo_de_folha', 'in', ['decimo_terceiro']),
            ('state', 'in', ['done','verify']),
        ])
        for line_id in holerite.line_ids:
            if line_id.code == 'IRPF':
                return line_id.total, holerite.line_ids.filtered(
                    lambda x: x.code == 'BASE_IRPF').total or 0.00
        return 0.0, 0.0

    def gerar_guias_pagamento(self):
        """
        Gerar dicionarios contendo os valores das GUIAS
        :return:
        """
        empresas = {}
        guia_pss = []
        darfs = {}
        contribuicao_sindical = {}
        darf_analitico = []

        for holerite in self.folha_ids:
            if not empresas.get(holerite.company_id.id):
                empresas.update({
                    holerite.company_id.id: {
                        'INSS_funcionarios': 0.00,
                        'INSS_empresa': 0.00,
                        'INSS_outras_entidades': 0.00,
                        'INSS_rat_fap': 0.00,
                    }
                })

            for line in holerite.line_ids:
                remuneracao = line.slip_id.line_ids.filtered(
                    lambda x: x.code == 'LIQUIDO')
                if line.code == 'CONTRIBUICAO_SINDICAL':
                    id_sindicato = \
                        line.slip_id.contract_id.partner_union.id or 0
                    if id_sindicato in contribuicao_sindical:
                        contribuicao_sindical[id_sindicato][
                            'contribuicao_sindicato'] += line.total
                        contribuicao_sindical[id_sindicato][
                            'qtd_contribuintes'] += 1
                        contribuicao_sindical[id_sindicato][
                            'total_remuneracao'] += remuneracao.total
                    else:
                        contribuicao_sindical[id_sindicato] = {}
                        contribuicao_sindical[id_sindicato][
                            'contribuicao_sindicato'] = line.total
                        contribuicao_sindical[id_sindicato][
                            'qtd_contribuintes'] = 1
                        contribuicao_sindical[id_sindicato][
                            'total_remuneracao'] = remuneracao.total
                elif line.code in ['INSS', 'INSS_13']:
                    empresas[line.slip_id.company_id.id][
                        'INSS_funcionarios'] += line.total
                elif line.code == 'INSS_EMPRESA':
                    empresas[line.slip_id.company_id.id][
                        'INSS_empresa'] += line.total
                elif line.code == 'INSS_OUTRAS_ENTIDADES':
                    empresas[line.slip_id.company_id.id][
                        'INSS_outras_entidades'] += line.total
                elif line.code == 'INSS_RAT_FAP':
                    empresas[line.slip_id.company_id.id][
                        'INSS_rat_fap'] += line.total

                #
                # GERAR DARF
                #
                # Para rubricas de PSS patronal gerar para cpf do
                # funcionario
                elif line.code in ['PSS_PATRONAL']:
                    guia_pss.append({
                        'code': '1850',
                        'valor': line.total,
                        'partner_id': line.employee_id.address_home_id})

                # Para rubricas de PSS do funcionario
                elif line.code in ['PSS']:
                    guia_pss.append({
                        'code': '1661',
                        'valor': line.total,
                        'partner_id': line.employee_id.address_home_id})
                    # partner_id = line.employee_id.address_home_id
                    # financial_move_darf = self.gerar_financial_move_darf(
                    #     '1661', line.total, partner_id)
                    # created_ids.append(financial_move_darf.id)

                # para gerar a DARF, identificar a categoria de contrato pois
                # cada categoria tem um código de emissao diferente
                elif line.code in ['IRPF', 'IRPF_13', 'IRPF_FERIAS',
                                   'IRPF_FERIAS_FERIAS',
                                   'IRRF_13_SALARIO_ESPECIFICA']:

                    codigo_darf = line.slip_id.contract_id.codigo_guia_darf

                    if darfs.get(codigo_darf):
                        darfs[codigo_darf] += line.total
                    else:
                        darfs.update({
                            codigo_darf: line.total
                        })

                    if 'FERIAS' in line.code:
                        base = 0.00
                    else:
                        base = line.slip_id.line_ids.filtered(
                            lambda x: x.code == 'BASE_IRPF').total

                    darf_analitico.append({
                        'nome': line.slip_id.contract_id.display_name,
                        'company_id': line.slip_id.contract_id.company_id.id,
                        'code': line.code,
                        'codigo_darf': codigo_darf,
                        'valor': line.total,
                        'base': base or 0.0,
                    })

            # buscar o valor do IRPF do holerite de 13º
            valor_13, base_13 = \
                self.buscar_IRPF_holerite_13(holerite.contract_id)
            darfs[codigo_darf] += valor_13

            if valor_13:
                darf_analitico.append({
                    'nome': line.slip_id.contract_id.display_name,
                    'code': line.code + '_DECIMO_TERCEIRO',
                    'valor': line.total,
                    'codigo_darf': codigo_darf,
                    'base': base_13,
                    'company_id': line.slip_id.contract_id.company_id.id,
                })

        return empresas, darfs, contribuicao_sindical, guia_pss, darf_analitico

    @api.multi
    def gerar_boletos(self):
        '''
        Criar ordem de pagamento para boleto de sindicato
        1. Configurar os dados para criação das financial.moves
        2. Criar os financial.moves
        '''
        #
        # Excluir registros financeiros anteriores
        #
        for boleto_id in self.boletos_ids:
            boleto_id.unlink()

        for record in self:

            created_ids = []

            empresas, darfs, contribuicao_sindical, pss, darf_analitico = \
                self.gerar_guias_pagamento()

            for company in empresas:
                dados_empresa = empresas[company]
                financial_move_gps = self.gerar_financial_move_gps(
                    company, dados_empresa)
                created_ids.append(financial_move_gps.id)

            for cod_darf in darfs:
                financial_move_darf = \
                    self.gerar_financial_move_darf(cod_darf, darfs[cod_darf])
                created_ids.append(financial_move_darf.id)

            for sindicato in contribuicao_sindical:
                vals = self.prepara_financial_move(
                    sindicato, contribuicao_sindical[sindicato])
                financial_move = self.env['financial.move'].create(vals)
                created_ids.append(financial_move.id)

            for guia_pss in pss:
                financial_move_darf = self.gerar_financial_move_darf(
                    guia_pss.get('code'), guia_pss.get('valor'),guia_pss.get('partner_id'))
                created_ids.append(financial_move_darf.id)

            return {
                'domain': "[('id', 'in', %s)]" % created_ids,
                'name': _("Guias geradas pelo SEFIP"),
                'res_ids': created_ids,
                'view_type': 'form',
                'view_mode': 'tree,form',
                'auto_search': True,
                'res_model': 'financial.move',
                'view_id': False,
                'search_view_id': False,
                'type': 'ir.actions.act_window'
            }

    @api.multi
    def action_sent(self):
        """
        Confirmar o Envio do Sefip:
        1. Validar se o sefip contem o relatorio em anexo
        2. Chamar a função que muda o status do holerite, liberando para pagamt
        """
        for record in self:
            record.valida_anexos()
            # Liberar holerites para pagamento
            for holerite in record.folha_ids:
                holerite.hr_verify_sheet()
            super(L10nBrSefip, record).action_sent()

    @api.multi
    def action_open(self):
        """
        Confirmar a geração do Sefip 
        """
        for record in self:
            record.criar_anexo_sefip()
        super(L10nBrSefip, record).action_open()

    @api.multi
    def gerar_sefip(self):
        for record in self:
            record.folha_ids = False
            record.folha_autonomo_ids = False
            sefip = SEFIP()

            if self.mes == '13':
                if self.modalidade_arquivo != '1':
                    raise ValidationError(
                        'Na competência 13 a Modalidade do Arquivo deverá ser igual a 1 ou 9.')

                if self.recolhimento_fgts != ' ':
                    raise ValidationError('Na competência 13 o Indicador de Recolhimento FGTS não deverá ser informado.')

            record.sefip = self._valida_tamanho_linha(
                record._preencher_registro_00(sefip))
            folha_ids = record._get_folha_ids()
            folha_autonomo_ids = record._get_folha_autonomos_ids()
            self._valida_centralizadora(folha_ids.mapped('company_id'))

            for company_id in folha_ids.mapped('company_id'):

                record.sefip += self._valida_tamanho_linha(
                    self._preencher_registro_10(company_id, sefip))

                record.sefip += self._valida_tamanho_linha(
                    self._preencher_registro_12(company_id, sefip))

                # Holerites da empresa
                folhas_da_empresa = folha_ids.filtered(
                    lambda r: r.company_id == company_id)
                # Holerites dos autonomos
                folhas_autonomo_empresa_ids = folha_autonomo_ids.filtered(
                    lambda r: r.company_id == company_id)

                # Acumulador para todos holerites. Dict para organizar
                # automaticamente a ordem
                holerites = {}
                # Acumulador para holerites
                for folha in folhas_da_empresa:
                    holerites[
                        punctuation_rm(folha.employee_id.pis_pasep)] = folha
                # Acumulador para autonomos
                for folha in folhas_autonomo_empresa_ids:
                    holerites[
                        punctuation_rm(folha.employee_id.pis_pasep)] = folha
                
                for key in sorted(list(holerites)):
                    record.sefip += self._valida_tamanho_linha(
                        record._preencher_registro_30(sefip, holerites[key]))

                    if holerites[key].tipo_de_folha == 'rescisao':
                        record.sefip += self._valida_tamanho_linha(
                           record._preencher_registro_32(sefip, holerites[key]))

            record.sefip += sefip._registro_90_totalizador_do_arquivo()

            # Setar a relação entre Holerite e o SEFIP
            for holerite in folha_ids:
                holerite.sefip_id = record.id

            # Setar a relação entre Autonomos e o SEFIP
            for holerite in folha_autonomo_ids:
                holerite.sefip_id = record.id

    def _preencher_registro_00(self, sefip):
        sefip.tipo_inscr_resp = '1' if \
            self.responsible_user_id.parent_id.is_company else '3'
        sefip.inscr_resp = self.responsible_user_id.parent_id.cnpj_cpf
        sefip.nome_resp = self.responsible_user_id.parent_id.legal_name
        sefip.nome_contato = (self.responsible_user_id.legal_name or
                              self.responsible_user_id.name)
        logadouro, bairro, cep, cidade, uf, telefone = \
            self._logadouro_bairro_cep_cidade_uf_telefone(
                'do responsável', self.company_id.partner_id
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
        if not self.company_id.supplier_partner_id:
            raise ValidationError(
                'Campo "Fornecedor do Sistema" não está preenchido nesta '
                'Empresa ! - Favor preenchê-lo antes de gerar a SEFIP'
            )
        elif not self.company_id.supplier_partner_id.cnpj_cpf:
            raise ValidationError(
                'Campo "CNPJ/CPF" do Fornecedor do Sistema '
                'não está preenchido! - Favor preenchê-lo '
                'antes de gerar a SEFIP'
            )
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
        sefip.emp_cod_centralizacao = company_id.centralizadora
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

    def _preencher_registro_12(self, company_id, sefip):

        tipo_inscr_empresa, inscr_empresa, cnae = self._tipo_inscricao_cnae(
            company_id
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
        Rubrica Base do FGTS
        As remunerações pagas após rescisão do contrato de trabalho e
        conforme determinação do Art. 466 da CLT,
        não devem vir acompanhadas das respectivas movimentações.
        """
        result = 0.00

        #
        # Não pode ser informado para a competência 13
        #
        if folha.tipo_de_folha == 'decimo_terceiro':
            return result

        # Em rescisoes A rubrica de base de FGTS totaliza o SALARIO e o
        # 13_salario. Para a SEFIP essa informações vão em campos separados.
        # Nesse caso buscaremos a rubrica BASE_INSS por ser uma totalizadora de
        # proventos. Ex.: casos como diferença salarial do mês anterior paga em
        # CCT, que deverão ser informadas na SEFIP
        if folha.tipo_de_folha == 'rescisao':
            return self._valor_rubrica(folha.line_ids, 'BASE_INSS')

        #
        # Para diretores buscar a base do INSS, pois a
        # estrutura de salario deles nao tem BASE_FGTS
        #
        categoria_diretoria = ('05', '11', '13')
        if folha.contract_id.categoria_sefip in categoria_diretoria:
            result += self._valor_rubrica(folha.line_ids, "BASE_INSS")

        # Para categorias que tem BASE_FGTS
        else:
            base_fgts = self._valor_rubrica(folha.line_ids, "BASE_FGTS")
            result +=  base_fgts if base_fgts > 0 else 0
            result += self._valor_rubrica(folha.line_ids, "BASE_FGTS_FERIAS")

            # Adiantamento de 13 vai em rubrica separada pro SEFIP
            # Como compoe a rubrica de BASE_FGTS, diminuir a de ADIANTAMENTO
            result -= \
                self._valor_rubrica(folha.line_ids, "ADIANTAMENTO_13_FERIAS")

        # Para Autonomos pegar as rubricas da categoria de Provento
        # Essa intervenção é temporária enquanto o calculo do RPA de autonomos
        # nao é automatizado e nao contem uma estrutura de salario
        if folha.contract_id.categoria_sefip == '13':
            result = sum(folha.line_ids.filtered(
                lambda line: line.category_id.code == 'PROVENTO').
                         mapped('total'))

        return result

    def _trabalhador_remun_13(self, folha):
        """ Registro 30. Item 17

        Rúbrica 13 Base do INSS (Somente na rescisão temos o 16 e o 17!)

        """

        if folha.contract_id.id == 22:
            pass

        result = 0.00

        # Na competencia 13 nao deve ser informado esses campos
        if folha.tipo_de_folha == 'decimo_terceiro':
            return result

        # Em rescisoes a Rubrica que paga o 13 Salario
        if folha.tipo_de_folha == 'rescisao':
            result += self._valor_rubrica(folha.line_ids, 'PROP13') - \
                      self._valor_rubrica(folha.line_ids, "DESCONTO_ADIANTAMENTO_13")

        # Se o funcionario adiantou ferias no holerite do mes
        result += self._valor_rubrica(folha.line_ids, 'ADIANTAMENTO_13_FERIAS')

        # Holerites de 13 gerados em dezembro tem a identificação do mes = 13
        # quando sao gerados como adiantamento, sao setados com o mes corrente
        mes_do_ano = [self.mes] if self.mes != '12' else [self.mes, '13']

        # Buscar folha de 13 salario
        folha_ids = self.env['hr.payslip'].search([
            ('ano', '=', self.ano),
            ('mes_do_ano', 'in', mes_do_ano),
            ('tipo_de_folha', 'in', ['decimo_terceiro']),
            ('is_simulacao', '=', False),
            ('state', 'in', ['done','verify']),
            ('contract_id', '=', folha.contract_id.id),
            # ('company_id.partner_id.cnpj_cpf', 'like', raiz)
        ], limit=1)

        if folha_ids:

            # Holerites de adiantamento de 13 gerados em maio para funcionarios
            # que nao adiantaram o 13 salario nas ferias, vem com o codigo
            #  de rubrica de PRIMEIRA_PARCELA_13
            result += self._valor_rubrica(
                folha_ids.line_ids, "PRIMEIRA_PARCELA_13")

            # Medias de substituicao no adiantamento de 13º Salario
            result += self._valor_rubrica(
                folha_ids.line_ids, "MEDIA_SALARIO_SUBSTI_ADIANT_13")

            result += self._valor_rubrica(
                folha_ids.line_ids, "DIF_MEDIA_SALARIO_SUBSTI_ADIANT_13")

            # Holerites de decimo terceiro em dez, a rubrica é SALARIO_13
            base_13 = \
                self._valor_rubrica(folha_ids.line_ids, "SALARIO_13") - \
                self._valor_rubrica(
                    folha_ids.line_ids, "DESCONTO_ADIANTAMENTO_13")

            result += base_13

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

        # return self._valor_rubrica(folha.line_ids, 'ADIANTAMENTO_13_FERIAS')

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
        vinculos_ids = folha.contract_id.contribuicao_inss_ids

        if not vinculos_ids:
            return 0.00

        return folha.line_ids.filtered(lambda x: x.code=='INSS').total or 0.00

    def _buscar_ocorrencias(self, folha):
        """ Estas informações devem ser lançadas na folha

        :param folha:
        :return:
        """
        # FIXME: Deste jeito não deu certo, pois existem afastamentos s/ data
        # folha_date_from = fields.Date.from_string(folha.date_from)
        # folha_date_to = fields.Date.from_string(folha.date_to)
        #
        # ocorrencia_aprovada_ids = folha.contract_id.afastamento_ids.filtered(
        #     lambda r: r.state == 'validate')
        # ocorrencias_no_periodo_ids = ocorrencia_aprovada_ids.filtered(
        #     lambda r: (folha_date_from >=
        #                fields.Date.from_string(r.data_inicio) and
        #                fields.Date.from_string(r.data_fim) <= folha_date_to))
        #
        # return ocorrencias_no_periodo_ids
        return []

    def _trabalhador_ocorrencia(self, folha):
        """ Registro 30. Item 19
        Ocorrencia: Acidente de trabalho, rescisão, afastamento por
        doença lic maternidade, ( situaçeõs que o funcionario deixa de
        trabalhar e o inss deverá assumir o pagamento do funcionário)

        Nao implementado:

         - Para empregado doméstico (Cat 06) e diretor não empregado
         (Cat 05) permitido apenas branco ou 05.
         -

        """
        #
        # Se contribuir INSS em outra entidade o código eh 05
        #
        if folha.contract_id.cnpj_empregador_cedente:
            return '05'

        # Aba Outros vinculos preenchida
        if folha.contract_id.contribuicao_inss_ids:
            return '05'

        #
        # Autônomos contribuem em outras entidades
        #
        if folha._name == 'hr.payslip.autonomo':
            return '05'

        # TODO:
        if folha.tipo_de_folha == 'rescisao':
            # FIXME:
            # return hr.payroll.structure.tipo_afastamento_sefip
            #print ("tipo_afastamento_sefip - Registro 30. Item 19")
            pass

        # ocorrencias_no_periodo_ids = self._buscar_ocorrencias(folha)
        #
        # if not ocorrencias_no_periodo_ids:
        #     return ocorrencia

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
        return multiplos_vinculos_ids

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
            return self._valor_rubrica(folha.line_ids, "BASE_INSS_13")

        if folha.tipo_de_folha == 'decimo_terceiro':
            if folha.base_inss:
                return folha.base_inss
            # No caso dos contratos que nao tem INSS
            # pegar a Rubrica do salario de decimo terceiro
            else:
                return self._valor_rubrica(folha.line_ids, "SALARIO_13")

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
        # if folha.tipo_de_folha == 'decimo_terceiro':
        #     return folha.base_inss
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
                folha.contract_id.date_start).strftime('%d%m%Y') or ''
        else:
            sefip.data_admissao = ''

        if codigo_categoria in ('01', '03', '04', '05', '06', '07', '11',
                                '12', '13', '19', '20', '21'):
            sefip.categoria_trabalhador = codigo_categoria or ''

        sefip.nome_trabalhador = folha.employee_id.name

        if codigo_categoria not in (
                '06', '13', '14', '15', '16', '17', '18', '22', '23',
                '24', '25'):
            sefip.matricula_trabalhador = folha.contract_id.matricula or ''

        if codigo_categoria in ('01', '03', '04', '06', '07', '26'):
            sefip.num_ctps = folha.employee_id.ctps or ''
            sefip.serie_ctps = folha.employee_id.ctps_series or ''
        else:
            sefip.num_ctps = ' ' * 7 or ''
            sefip.serie_ctps = ' ' * 5 or ''

        if codigo_categoria in ('01', '03', '04', '05', '06', '07'):
            # Item 13: Data de opção do FGtS, é sempre a data de contratação!
            sefip.data_de_opcao = fields.Datetime.from_string(
                folha.contract_id.date_start).strftime('%d%m%Y') or ''
        else:
            sefip.data_de_opcao = '      '

        if codigo_categoria in ('01', '02', '03', '04', '05', '06', '07',
                                '12', '19', '20', '21', '26') and \
                folha.employee_id.birthday:
            sefip.data_de_nascimento = fields.Datetime.from_string(
                folha.employee_id.birthday).strftime('%d%m%Y')
        else:
            sefip.data_de_nascimento = '      '

        if not folha.contract_id.job_id:
            raise ValidationError("Contrato " + folha.contract_id.name + " faltando campo função !")

        if codigo_categoria in '06':
            sefip.trabalhador_cbo = '05121'
        else:
            sefip.trabalhador_cbo = '0' + \
                                    folha.contract_id.job_id.cbo_id.code[:4]
        # Revisar daqui para a frente

        sefip.trabalhador_remun_13 = \
            self._trabalhador_remun_13(folha) or ''
        sefip.trabalhador_remun_sem_13 = \
            self._trabalhador_remun_sem_13(folha) or ''

        sefip.trabalhador_classe_contrib = \
            self._trabalhador_classe_contrib(folha) or ''

        sefip.trabalhador_ocorrencia = self._trabalhador_ocorrencia(folha) or ''
        sefip.trabalhador_valor_desc_segurado = \
            self._trabalhador_valor_desc_segurado(folha) or ''
        sefip.trabalhador_remun_base_calc_contribuicao_previdenciaria = \
            self._trabalhador_remun_base_calc_contribuicao_previdenciaria(
                folha) or ''
        sefip.trabalhador_base_calc_13_previdencia_competencia = \
            self._trabalhador_base_calc_13_previdencia_competencia(folha) or ''
        sefip.trabalhador_base_calc_13_previdencia_GPS = \
            self._trabalhador_base_calc_13_previdencia_GPS(folha) or ''

        return sefip._registro_30_registro_do_trabalhador()

    def _preencher_registro_32(self, sefip, folha):
        """

        Registro de movimentação de Trabalhador

        """
        tipo_afastamento = folha.struct_id.tipo_afastamento_sefip
        sefip.trabalhador_codigo_movimentacao = tipo_afastamento or '  '
        sefip.trabalhador_data_movimentacao = \
            formata_data(folha.data_afastamento) or ''
        # Gerado GRRF
        sefip.trabalhador_indic_recolhimento_fgts = 'N'

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
        sefip_attachment_obj = self.env['l10n_br.hr.sefip.attachments']

        try:
            file_attc = open(path_arquivo_temp, 'r')
            attc = file_attc.read()

            attachment_data = {
                'name': nome_do_arquivo,
                'datas_fname': nome_do_arquivo,
                'datas': base64.b64encode(attc),
                'res_model': 'l10n_br.hr.sefip.attachments',
            }

            if 'sent' in [line.type for line in self.related_attachment_ids]:
                for line in self.related_attachment_ids:
                    if line.type == 'sent':
                        attach_id = attachment_obj.create(attachment_data)
                        line.attachment_ids = False
                        line.attachment_ids = [attach_id.id]
            else:
                sefip_attachment_data = {
                    'name': 'Arquivo SEFIP',
                    'sefip_id': self.id,
                    'attachment_ids': [(0, 0, attachment_data)],
                    'type': 'sent'
                }
                sefip_attachment_obj.create(sefip_attachment_data)

            file_attc.close()

        except:
            raise Warning(
                _('Impossível gerar Anexo do %s' % nome_do_arquivo))
