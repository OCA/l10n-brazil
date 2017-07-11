# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Luiz Felipe do Divino Costa <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import codecs
import logging
from datetime import datetime

from openerp import api, models, fields

_logger = logging.getLogger(__name__)
try:
    from cnab240.bancos import bancodobrasil
    from cnab240.tipos import Arquivo
except ImportError as err:
    _logger.debug = (err)

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

    @api.multi
    def processar_arquivo_retorno(self):
        arquivo_retono = base64.b64decode(self.arquivo_retorno)
        f = open('/tmp/cnab_retorno.ret', 'wb')
        f.write(arquivo_retono)
        f.close()
        arquivo_retono = codecs.open('/tmp/cnab_retorno.ret', encoding='ascii')
        arquivo_parser = Arquivo(bancodobrasil, arquivo=arquivo_retono)
        data_arquivo = str(arquivo_parser.header.arquivo_data_de_geracao)
        self.data_arquivo = fields.Date.from_string(
            data_arquivo[4:] + "-" + data_arquivo[2:4] + "-" + data_arquivo[
                                                               0:2]
        )
        self.bank_account_id = self.env['res.partner.bank'].search(
            [('acc_number', '=', arquivo_parser.header.cedente_conta)]).id
        self.num_lotes = arquivo_parser.trailer.totais_quantidade_lotes
        self.num_eventos = arquivo_parser.trailer.totais_quantidade_registros
        for lote in arquivo_parser.lotes:
            account_bank_id_lote = self.env['res.partner.bank'].search(
                [('acc_number', '=', lote.header.cedente_conta)]
            ).id
            vals = {
                'account_bank_id': account_bank_id_lote,
                'empresa_inscricao_numero':
                    str(lote.header.empresa_inscricao_numero),
                'empresa_inscricao_tipo':
                    TIPO_INSCRICAO_EMPRESA[lote.header.empresa_inscricao_tipo],
                'servico_operacao':
                    TIPO_OPERACAO[lote.header.servico_operacao],
                'tipo_servico': TIPO_SERVICO[str(lote.header.servico_servico)],
                'mensagem': lote.header.mensagem1,
                'qtd_registros': lote.trailer.quantidade_registros,
                'total_valores': float(lote.trailer.somatoria_valores),
                'cnab_id': self.id,
            }
            lote_id = self.env['l10n.br.cnab.lote'].create(vals)
            for evento in lote.eventos:
                data_evento = str(
                    evento.credito_data_real)
                data_evento = fields.Date.from_string(
                    data_evento[4:] + "-" + data_evento[
                                            2:4] + "-" + data_evento[0:2]
                )
                account_bank_id_lote = self.env['res.partner.bank'].search(
                    [('acc_number', '=', evento.favorecido_conta)]).id
                favorecido_partiner = self.env['res.partner'].search(
                    [('name', '=', evento.favorecido_nome)]).id
                vals_evento = {
                    'data_real_pagamento': data_evento,
                    'segmento': evento.servico_segmento,
                    'favorecido_nome': favorecido_partiner,
                    'favorecido_conta_bancaria': account_bank_id_lote,
                    'nosso_numero': str(evento.credito_nosso_numero),
                    'seu_numero': evento.credito_seu_numero,
                    'tipo_moeda': evento.credito_moeda_tipo,
                    'valor_pagamento': evento.credito_valor_pagamento,
                    'ocorrencias': evento.ocorrencias,
                    'lote_id': lote_id.id,
                }
                self.env['l10n.br.cnab.evento'].create(vals_evento)
        return self.write({'state': 'done'})

    @api.multi
    @api.depends('data')
    def _get_rec_name(self):
        if not self.display_name:
            for rec in self:
                cnab_ids = self.search([('data', '=', rec.data)])
                rec.display_name = rec.data + " - " + str(len(cnab_ids) + 1)

    arquivo_retorno = fields.Binary(string='Arquivo Retorno')
    data = fields.Date(
        string="Data CNAB",
        default=datetime.now()
    )
    display_name = fields.Char(
        string="Name",
        compute=_get_rec_name,
        store=True,
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


class L10nBrHrCnabEvento(models.Model):
    _name = "l10n.br.cnab.evento"

    data_real_pagamento = fields.Datetime(string="Data Real do Pagamento")
    segmento = fields.Char(string="Segmento")
    favorecido_nome = fields.Many2one(
        string="Favorecido",
        comodel_name="res.partner"
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
    payment_line_id = fields.Many2one(
        string="Payment Line",
        comodel_name="payment.line",
    )
    lote_id = fields.Many2one(
        string="Lote",
        comodel_name="l10n.br.cnab.lote",
    )
