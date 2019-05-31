# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author  Luiz Felipe do Divino Costa <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from datetime import datetime
from ..constantes import CODIGO_OCORRENCIAS
from ..febraban.cnab import Cnab

from odoo import api, models, fields, exceptions

_logger = logging.getLogger(__name__)

STATE = [
    ('draft', 'Novo'),
    ('done', 'Processado'),
]

TIPO_OPERACAO = {
    'C': u'Lançamento a Crédito',
    'D': u'Lançamento a Débito',
    'E': u'Extrato para Conciliação',
    'G': u'Extrato para Gestão de Caixa',
    'I': u'Informações de Títulos Capturados do Próprio Banco',
    'R': u'Arquivo Remessa',
    'T': u'Arquivo Retorno',
}

TIPO_SERVICO = {
    '01': 'Cobrança',
    '03': 'Boleto de Pagamento Eletrônico',
    '04': 'Conciliação Bancária',
    '05': 'Débitos',
    '06': 'Custódia de Cheques',
    '07': 'Gestão de Caixa',
    '08': 'Consulta/Informação Margem',
    '09': 'Averbação da Consignação/Retenção',
    '10': 'Pagamento Dividendos',
    '11': 'Manutenção da Consignação',
    '12': 'Consignação de Parcelas',
    '13': 'Glosa da Consignação (INSS)',
    '14': 'Consulta de Tributos a pagar',
    '20': 'Pagamento Fornecedor',
    '22': 'Pagamento de Contas, Tributos e Impostos',
    '23': 'Interoperabilidade entre Contas de Instituições de Pagamentos',
    '25': 'Compror',
    '26': 'Compror Rotativo',
    '29': 'Alegação do Pagador',
    '30': 'Pagamento Salários',
    '32': 'Pagamento de honorários',
    '33': 'Pagamento de bolsa auxílio',
    '34': 'Pagamento de prebenda (remuneração a padres e sacerdotes)',
    '40': 'Vendor',
    '41': 'Vendor a Termo',
    '50': 'Pagamento Sinistros Segurados',
    '60': 'Pagamento Despesas Viajante em Trânsito',
    '70': 'Pagamento Autorizado',
    '75': 'Pagamento Credenciados',
    '77': 'Pagamento de Remuneração',
    '80': 'Pagamento Representantes / Vendedores Autorizados',
    '90': 'Pagamento Benefícios',
    '98': 'Pagamentos Diversos',
}

TIPO_INSCRICAO_EMPRESA = {
    0: 'Isento / Não informado',
    1: 'CPF',
    2: 'CGC / CNPJ',
    3: 'PIS / PASEP',
    9: 'Outros',
}


class L10nBrHrCnab(models.Model):
    _name = "l10n.br.cnab"
    _rec_name = "display_name"


    def _busca_conta(self, banco, agencia, conta):
        return self.env['res.partner.bank'].search([
            # ('acc_number', '=', str(banco)),
            ('bra_number', '=', str(agencia)),
            ('acc_number', '=', str(conta))
        ]).id

    def _cria_lote(self, header, lote, evento, trailer):

        if lote.header:
            lote_bank_account_id = self._busca_conta(
                lote.header.codigo_do_banco,
                lote.header.cedente_agencia,
                lote.header.cedente_conta,
            ).id
        else:
            lote_bank_account_id = self.bank_account_id

        vals = {
            'account_bank_id': lote_bank_account_id.id,
            # 'empresa_inscricao_numero':
            #     str(header.empresa_inscricao_numero),
            # 'empresa_inscricao_tipo':
            #     TIPO_INSCRICAO_EMPRESA[header.empresa_inscricao_tipo],
            # 'servico_operacao': TIPO_OPERACAO[header.servico_operacao],
            # 'tipo_servico': TIPO_SERVICO[str(header.servico_servico)],
            # 'mensagem': header.mensagem1,
            # 'total_valores': float(trailer.somatoria_valores),
            'servico_operacao': header.literal_retorno,
            'tipo_servico': header.literal_servico,
            'qtd_registros': trailer.totais_quantidade_registros,
            'total_valores': float(trailer.valor_total_titulos/100),
            'cnab_id': self.id,
        }

        lote_id = self.env['l10n.br.cnab.lote'].create(vals)

        return lote_id, lote_bank_account_id


    @api.multi
    def processar_arquivo_retorno(self):
        arquivo_parser = Cnab.detectar_retorno(self.arquivo_retorno)
        # if not arquivo_parser.header.arquivo_codigo == u'2':
        #     raise exceptions.Warning(
        #         u"Este não é um arquivo de retorno!"
        #     )
        data_arquivo = str(arquivo_parser.header.arquivo_data_de_geracao)
        self.data_arquivo = datetime.strptime(data_arquivo, "%d%m%y")

        self.bank_account_id = self._busca_conta(
            arquivo_parser.header.codigo_do_banco,
            arquivo_parser.header.cedente_agencia,
            arquivo_parser.header.cedente_conta,
        )

        self.num_lotes = len(arquivo_parser.lotes)
        self.num_eventos = arquivo_parser.trailer.totais_quantidade_registros
        for lote in arquivo_parser.lotes:

            header  = lote.header or arquivo_parser.header
            trailer  = lote.trailer or arquivo_parser.trailer

            lote_id = False

            for evento in lote.eventos:
                if not lote_id:
                    lote_id, lote_bank_account_id = self._cria_lote(
                        header, lote, evento, trailer)

                data_evento = str(
                    evento.credito_data_real)
                data_evento = fields.Date.from_string(
                    data_evento[4:] + "-" + data_evento[2:4] + "-" +
                    data_evento[0:2]
                )
                lote_bank_account_id = self.env['res.partner.bank'].search(
                    [
                        ('bra_number', '=', evento.favorecido_agencia),
                        ('bra_number_dig', '=', evento.favorecido_agencia_dv),
                        ('acc_number', '=', evento.favorecido_conta),
                        ('acc_number_dig', '=', evento.favorecido_conta_dv)
                    ])
                lote_bank_account_id = lote_bank_account_id.ids[0] \
                    if lote_bank_account_id else False
                favorecido_partner = self.env['res.partner.bank'].search(
                    [('owner_name', 'ilike', evento.favorecido_nome)]
                )
                favorecido_partner = favorecido_partner[0].partner_id.id \
                    if favorecido_partner else False
                bank_payment_line_id = self.env['bank.payment.line'].search(
                    [
                        ('name', '=', evento.credito_seu_numero)
                    ]
                )
                ocorrencias_dic = dict(CODIGO_OCORRENCIAS)
                ocorrencias = [
                    evento.ocorrencias[0:2],
                    evento.ocorrencias[2:4],
                    evento.ocorrencias[4:6],
                    evento.ocorrencias[6:8],
                    evento.ocorrencias[8:10]
                ]
                vals_evento = {
                    'data_real_pagamento': data_evento,
                    'segmento': evento.servico_segmento,
                    'favorecido_nome': favorecido_partner,
                    'favorecido_conta_bancaria': lote_bank_account_id,
                    'nosso_numero': str(evento.credito_nosso_numero),
                    'seu_numero': evento.credito_seu_numero,
                    'tipo_moeda': evento.credito_moeda_tipo,
                    'valor_pagamento': evento.credito_valor_pagamento,
                    'ocorrencias': evento.ocorrencias,
                    'str_motiv_a': ocorrencias_dic[ocorrencias[0]] if
                    ocorrencias[0] else '',
                    'str_motiv_b': ocorrencias_dic[ocorrencias[1]] if
                    ocorrencias[1] else '',
                    'str_motiv_c': ocorrencias_dic[ocorrencias[2]] if
                    ocorrencias[2] else '',
                    'str_motiv_d': ocorrencias_dic[ocorrencias[3]] if
                    ocorrencias[3] else '',
                    'str_motiv_e': ocorrencias_dic[ocorrencias[4]] if
                    ocorrencias[4] else '',
                    'lote_id': lote_id.id,
                    'bank_payment_line_id': bank_payment_line_id.id,
                }
                self.env['l10n.br.cnab.evento'].create(vals_evento)
                if evento.ocorrencias and bank_payment_line_id:
                    if '00' in ocorrencias:
                        bank_state = 'paid'
                        cnab_state = 'accepted'

                    else:
                        bank_state = 'exception'
                        cnab_state = 'not_accepted'

                    bank_payment_line_id.state2 = bank_state
                    for payment_line in bank_payment_line_id.payment_line_ids:
                        payment_line.move_line_id.state_cnab = cnab_state

        return self.write({'state': 'done'})

    @api.multi
    def _get_name(self, data):
        cnab_ids = self.search([('data', '=', data)])
        return data + " - " + (
            str(len(cnab_ids) + 1) if cnab_ids else '1'
        )

    @api.model
    def create(self, vals):
        name = self._get_name(vals['data'])
        vals.update({'name': name})
        return super(L10nBrHrCnab, self).create(vals)

    arquivo_retorno = fields.Binary(string='Arquivo Retorno')
    data = fields.Date(
        string="Data CNAB",
        required=True,
        default=datetime.now()
    )
    name = fields.Char(
        string="Name",
    )
    lote_id = fields.One2many(
        string="Lotes",
        comodel_name="l10n.br.cnab.lote",
        inverse_name="cnab_id"
    )
    state = fields.Selection(
        string=u"Estágio",
        selection=STATE,
        default="draft",
    )
    data_arquivo = fields.Datetime(
        string="Data Criação no Banco",
    )
    bank_account_id = fields.Many2one(
        string="Conta cedente",
        comodel_name="res.partner.bank",
    )
    num_lotes = fields.Integer(
        string=u"Número de Lotes",
    )
    num_eventos = fields.Integer(
        string=u"Número de Eventos",
    )


class L10nBrHrCnabLote(models.Model):
    _name = "l10n.br.cnab.lote"

    account_bank_id = fields.Many2one(
        string=u"Conta Bancária",
        comodel_name="res.partner.bank",
    )
    empresa_inscricao_numero = fields.Char(string=u"Número de Inscrição")
    empresa_inscricao_tipo = fields.Char(string=u"Tipo de Inscrição")
    servico_operacao = fields.Char(string=u"Tipo de Operação")
    tipo_servico = fields.Char(strin=u"Tipo do Serviço")
    mensagem = fields.Char(string="Mensagem")
    qtd_registros = fields.Integer(string="Quantidade de Registros")
    total_valores = fields.Float(string="Valor Total")
    evento_id = fields.One2many(
        string="Eventos",
        comodel_name="l10n.br.cnab.evento",
        inverse_name="lote_id",
    )
    cnab_id = fields.Many2one(
        string="CNAB",
        comodel_name="l10n.br.cnab"
    )
    state = fields.Selection(
        string="State",
        related="cnab_id.state",
        selection=STATE,
        default="draft",
    )


class L10nBrHrCnabEvento(models.Model):
    _name = "l10n.br.cnab.evento"

    data_real_pagamento = fields.Datetime(string="Data Real do Pagamento")
    segmento = fields.Char(string="Segmento")
    favorecido_nome = fields.Many2one(
        string="Favorecido",
        comodel_name="res.partner"
    )
    favorecido_conta_bancaria = fields.Many2one(
        string=u"Conta Bancária",
        comodel_name="res.partner.bank",
    )
    nosso_numero = fields.Char(string=u"Nosso Número")
    seu_numero = fields.Char(string=u"Seu Número")
    tipo_moeda = fields.Char(string=u"Tipo de Moeda")
    valor_pagamento = fields.Float(string="Valor do Pagamento")
    ocorrencias = fields.Char(string=u"Ocorrências")
    str_motiv_a = fields.Char(u'Motivo da ocorrência 01')
    str_motiv_b = fields.Char(u'Motivo de ocorrência 02')
    str_motiv_c = fields.Char(u'Motivo de ocorrência 03')
    str_motiv_d = fields.Char(u'Motivo de ocorrência 04')
    str_motiv_e = fields.Char(u'Motivo de ocorrência 05')
    bank_payment_line_id = fields.Many2one(
        string="Bank Payment Line",
        comodel_name="bank.payment.line",
    )
    lote_id = fields.Many2one(
        string="Lote",
        comodel_name="l10n.br.cnab.lote",
    )
    state = fields.Selection(
        string="State",
        related="lote_id.state",
        selection=STATE,
        default="draft",
    )
