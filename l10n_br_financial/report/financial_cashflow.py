# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _, tools
from ..models.financial_move_model import (
    FINANCIAL_MOVE,
    FINANCIAL_STATE,
    FINANCIAL_TYPE
)


class FinancialCashflow(models.Model):
    _name = 'financial.cashflow'
    _auto = False
    # _order = 'amount_cumulative_balance'
    _order = 'business_due_date, id'

    amount_cumulative_balance = fields.Monetary(
        string=u"Balance",
    )
    amount_debit = fields.Monetary(
        string=u"Debit",
    )
    amount_credit = fields.Monetary(
        string=u"Credit",
    )
    state = fields.Selection(
        selection=FINANCIAL_STATE,
        string='Status',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Company',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
    )
    document_number = fields.Char(
        string=u"Document Nº",
    )
    document_item = fields.Char(
        string=u"Document item",
    )
    document_date = fields.Date(
        string=u"Document date",
    )
    amount_document = fields.Monetary(
        string=u"Document amount",
    )
    due_date = fields.Date(
        string=u"Due date",
    )
    move_type = fields.Selection(
        selection=FINANCIAL_TYPE,
    )
    business_due_date = fields.Date(
        string='Business due date',
    )
    payment_mode = fields.Many2one(
        comodel_name='payment.mode',  # FIXME:
    )
    payment_term = fields.Many2one(
        comodel_name='payment.term',  # FIXME:
    )

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow_credit AS
                SELECT
                    financial_move.create_date,
                    financial_move.id,
                    financial_move.document_number,
                    financial_move.document_item,
                    financial_move.move_type,

                    financial_move.state,
                    financial_move.business_due_date,
                    financial_move.document_date,
                    financial_move.payment_mode,
                    financial_move.payment_term,

                    financial_move.due_date,
                    financial_move.partner_id,
                    financial_move.currency_id,
                    coalesce(financial_move.amount_document, 0)
                        AS amount_document,
                    coalesce(financial_move.amount_document, 0)
                        AS amount_credit,
                    0 AS amount_debit,
                    coalesce(financial_move.amount_document, 0)
                        AS amount_balance
                FROM
                    public.financial_move
                WHERE
                    financial_move.move_type = 'r';
        """)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow_debit AS
                SELECT
                    financial_move.create_date,
                    financial_move.id,
                    financial_move.document_number,
                    financial_move.document_item,
                    financial_move.move_type,

                    financial_move.state,
                    financial_move.business_due_date,
                    financial_move.document_date,
                    financial_move.payment_mode,
                    financial_move.payment_term,

                    financial_move.due_date,
                    financial_move.partner_id,
                    financial_move.currency_id,
                    coalesce(financial_move.amount_document, 0)
                        AS amount_document,
                    0 AS amount_credit,
                    (-1) * coalesce(financial_move.amount_document, 0)
                        AS amount_debit,
                    (-1) * coalesce(financial_move.amount_document, 0)
                        AS amount_balance
                FROM
                    public.financial_move
                WHERE
                    financial_move.move_type = 'p';
        """)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow_base AS
                SELECT
                    c.create_date,
                    c.id,
                    c.document_number,
                    c.move_type,
                    c.state,
                    c.business_due_date,
                    c.document_date,
                    c.payment_mode,
                    c.payment_term,
                    c.due_date,
                    c.partner_id,
                    c.currency_id,
                    c.amount_document,
                    c.amount_credit,
                    c.amount_debit,
                    c.amount_balance
                FROM
                    financial_cashflow_credit c

                UNION ALL

                SELECT
                    d.create_date,
                    d.id,
                    d.document_number,
                    d.move_type,
                    d.state,
                    d.business_due_date,
                    d.document_date,
                    d.payment_mode,
                    d.payment_term,
                    d.due_date,
                    d.partner_id,
                    d.currency_id,
                    d.amount_document,
                    d.amount_credit,
                    d.amount_debit,
                    d.amount_balance
                FROM
                    financial_cashflow_debit d;
        """)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow AS
                SELECT
                    b.create_date,
                    b.id,
                    b.document_number,
                    b.move_type,
                    b.state,
                    b.business_due_date,
                    b.document_date,
                    b.payment_mode,
                    b.payment_term,
                    b.due_date,
                    b.partner_id,
                    b.currency_id,
                    b.amount_document,
                    b.amount_credit,
                    b.amount_debit,
                    b.amount_balance,
                    SUM(b.amount_balance)
                    OVER (order by b.business_due_date, b.id)
                        AS amount_cumulative_balance
                    -- aqui deveria haver um campo balance_date ou algo assim
                    -- que seria a data de crédito/débito efetivo na conta
                    -- pois boletos e cheques tem data de crédito d+1 ou d+2
                    -- após o depósito/pagamento. Exemplo:
                    -- over(order by b.data_credito_debito)
                FROM
                    financial_cashflow_base b;
        """)
