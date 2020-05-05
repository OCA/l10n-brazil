# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants.payment import (
    BANDEIRA_CARTAO,
    FORMA_PAGAMENTO,
    INTEGRACAO_CARTAO,
    INTEGRACAO_CARTAO_NAO_INTEGRADO,
)


class FiscalPayment(models.Model):
    _name = "l10n_br_fiscal.payment"
    _description = "Fiscal Payment"
    _order = 'document_id, sequence, payment_term_id'

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Documento',
        ondelete='cascade',
    )
    sequence = fields.Integer(
        default=10,
    )
    payment_term_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.payment.term',
        string='Condição de pagamento',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
    )
    amount = fields.Monetary(
        string='Valor',
    )
    amount_change = fields.Monetary(
        string='Troco',
    )
    autorizacao = fields.Char(
        string='Autorização nº',
        size=20,
    )
    line_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.payment.line',
        inverse_name='payment_id',
        string='Duplicatas',
    )
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento',
    )
    bandeira_cartao = fields.Selection(
        selection=BANDEIRA_CARTAO,
        string='Bandeira do cartão',
    )
    integracao_cartao = fields.Selection(
        selection=INTEGRACAO_CARTAO,
        string='Integração do cartão',
        default=INTEGRACAO_CARTAO_NAO_INTEGRADO,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Operadora do cartão',
        ondelete='restrict',
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
    )

    def _get_document_id(self):
        if (self.env.context.get('active_model') == 'l10n_br_fiscal.document' and
                self.env.context.get('active_id')):
            return self.env['l10n_br_fiscal.document'].browse(
                self.env.context.get('active_id')
            )
        return self.document_id

    def _get_active_id(self):
        """ Override this method at invoice, sale, puchase and etc.
        :return
                True if you can correctly set the origin of this payment
                False if you can't.
        """
        return self._get_document_id()

    def _get_date(self):
        if self.document_id:
            return self.document_id.date

    def _prepare_line_id(self, communication, date_maturity, amount):
        vals = dict()
        vals['communication'] = communication
        vals['date_maturity'] = date_maturity
        vals['amount'] = amount
        vals['payment_id'] = self.id
        vals['currency_id'] = self.currency_id.id
        vals['company_id'] = self.company_id.id
        return vals

    @api.onchange('payment_term_id', 'amount', 'currency_id')
    def _onchange_payment_term_id(self):

        if not (self.payment_term_id and self._get_active_id()):
            return

        payment_term_list = self.payment_term_id.with_context(
            currency_id=self.currency_id.id
        ).compute(value=self.amount or 0, date_ref=self._get_date())[0]

        if payment_term_list:
            line_ids = [
                (5, False, {}),
            ]

            communication = 1
            for date_maturity, amount in payment_term_list:
                line_ids.append((
                    0,
                    False,
                    self._prepare_line_id(communication, date_maturity, amount)
                ))
                communication += 1

            self.line_ids = line_ids

        self.forma_pagamento = self.payment_term_id.forma_pagamento
        self.bandeira_cartao = self.payment_term_id.bandeira_cartao
        self.integracao_cartao = self.payment_term_id.integracao_cartao
        self.partner_id = self.payment_term_id.partner_id
        self.cnpj_cpf = (
            self.payment_term_id.partner_id and
            self.payment_term_id.partner_id.cnpj_cpf or False
        )
