# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, _

from ..febraban.boleto.document import Boleto
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


ESTADOS_CNAB = [
    ('draft', u'Inicial'),
    ('added', u'Adicionada à ordem de pagamento'),
    ('added_paid', u'Adicionada para Baixa'),
    ('exported', u'Exportada'),
    ('exporting_error', u'Erro ao exportar'),
    ('accepted', u'Aceita'),
    ('accepted_hml', u'Aceita em Homologação'),
    ('not_accepted', u'Não aceita pelo banco'),
    ('done', u'Concluído'),
]

SITUACAO_PAGAMENTO = [
    ('inicial', 'Inicial'),
    ('aberta', 'Aberta'),
    ('paga', 'Paga'),
    ('liquidada', 'Liquidada'),
    ('baixa', 'Baixa Simples'),
    ('baixa_liquidacao', 'Baixa por Liquidação em Dinheiro'),
]


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    state_cnab = fields.Selection(
        ESTADOS_CNAB, u'Estados CNAB', default='draft')
    date_payment_created = fields.Date(
        u'Data da criação do pagamento', readonly=True)
    nosso_numero = fields.Char(
        string=u'Nosso Numero',
    )
    numero_documento = fields.Char(
        string=u'Número documento'
    )
    identificacao_titulo_empresa = fields.Char(
        string=u'Identificação Titulo Empresa',
    )
    situacao_pagamento = fields.Selection(
        selection=SITUACAO_PAGAMENTO,
        string=u'Situação do Pagamento',
        default='inicial'
    )
    instrucoes = fields.Text(
        string=u'Instruções de cobrança',
        readonly=True,
    )

    residual = fields.Monetary(
        string=u'Valor Residual',
        default=0.0,
        currency_field='company_currency_id'
    )

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        vals = super(AccountMoveLine, self)._prepare_payment_line_vals(
            payment_order
        )
        vals['nosso_numero'] = self.nosso_numero
        vals['numero_documento'] = self.numero_documento
        vals['identificacao_titulo_empresa'] = \
            self.identificacao_titulo_empresa

        if self.invoice_id.state == 'paid':
            vals['amount_currency'] = self.credit or self.debit

        return vals

    @api.multi
    def create_payment_line_from_move_line(self, payment_order):
        """
        Altera estado do cnab para adicionado a ordem
        :param payment_order:
        :return:
        """
        state_cnab = 'added'
        if self.invoice_id.state == 'paid':
            state_cnab = 'added_paid'

        self.state_cnab = state_cnab

        return super(AccountMoveLine, self).create_payment_line_from_move_line(
            payment_order
        )

    @api.multi
    def generate_boleto(self, validate=True):
        boleto_list = []

        for move_line in self:

            if validate and move_line.state_cnab not in \
                    ['accepted', 'accepted_hml']:
                if move_line.state_cnab == 'not_accepted':
                    raise UserError(_(
                        u'Essa fatura foi transmitida com erro ao banco, '
                        u'é necessário corrigí-la e reenviá-la.'
                    ))
                raise UserError(_(
                    u'Antes de imprimir o boleto é necessário transmitir a '
                    u'fatura para registro no banco.'
                ))

            boleto = Boleto.getBoleto(
                move_line, move_line.nosso_numero
            )

            # Se a cobrança tiver sido emitida em homologação
            if move_line.state_cnab == 'accepted_hml':
                boleto.boleto.instrucoes.append(_(
                    u'Boleto emitido em homologacao! Sem valor fiscal!'))

            boleto_list.append(boleto.boleto)
        return boleto_list

    @api.multi
    def _update_check(self):

        if self._context.get("reprocessing"):
            return True

        return super(AccountMoveLine, self)._update_check()
