# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _

from .account_invoice_term import (
    FORMA_PAGAMENTO_SEM_PAGAMENTO,
)



class AccountInvoicePayment(models.Model):
    _name = b'account.invoice.payment'
    _description = 'Dados de pagamento'
    _order = 'invoice_id, sequence, payment_term_id'

    sequence = fields.Integer(
        default=10,
    )
    date = fields.Date(
        string='Data de referência',
        readonly=True,
    )
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Condição de pagamento',
        ondelete='restrict',
        domain=[('forma_pagamento', '!=', False)],
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
    )
    amount = fields.Float(
        string='Amount',
    )
    autorizacao = fields.Char(
        string='Autorização nº',
        size=20,
    )
    nsu = fields.Char(
        string='NSU',
        help='Numero sequencial unico',
    )
    ind_forma_pagamento = fields.Selection(
        related='payment_term_id.ind_forma_pagamento',
        store=True,
    )
    forma_pagamento = fields.Selection(
        related='payment_term_id.forma_pagamento',
        store=True,
    )
    card_brand = fields.Selection(
        related='payment_term_id.card_brand',
        store=True,
    )
    card_integration = fields.Selection(
        related='payment_term_id.card_integration',
        store=True,
    )
    partner_id = fields.Many2one(
        related='payment_term_id.partner_id',
        store=True,
        ondelete='restrict',
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
        related='partner_id.cnpj_cpf',
        readonly=True,
    )
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice',
        ondelete='set null',  # Allow use the same model in sale and purchase
    )
    item_ids = fields.One2many(
        comodel_name='account.invoice.payment.line',
        inverse_name='payment_id',
        string='Duplicatas',
    )

    def _set_parent(self, field_parent, field_parent_id):
        date = False

        if field_parent == 'invoice_id':
            date = field_parent_id.date_invoice
            self.invoice_id = field_parent_id
        return date or fields.Date.context_today(field_parent_id)

    @api.onchange('payment_term_id', 'amount', 'item_ids', 'date')
    def onchange_payment_term_id(self):

        if not (self.payment_term_id and self.amount):
            return

        field_parent = self.env.context.get('field_parent')

        if field_parent:
            field_parent_id = getattr(self, field_parent)
            self.date = self._set_parent(field_parent, field_parent_id)[:10]

        pterm_list = self.payment_term_id.compute(self.amount, self.date)[0]

        self.forma_pagameto = self.payment_term_id.forma_pagamento

        item_ids = [
            (5, 0, {})
        ]

        for term in pterm_list:
            item_ids.append(
                (0, 0, {
                    'payment_id': self.id,
                    'date_due': term[0],
                    'amount_original': term[1],
                    'amount_discount': 0.00,
                    'amount_net': term[1],
                })
            )
        self.item_ids = item_ids

    def default_payment_term(self, payment_term_id, amount=0.00, object=False, date=False):

        if not (payment_term_id.forma_pagamento ==
                FORMA_PAGAMENTO_SEM_PAGAMENTO):

            values = {
                'payment_term_id': payment_term_id.id,
                'amount': amount,
                'date': fields.Date.today(self),
            }
            term = self.create(values)
            term._onchange_payment_term_id()

            return term
