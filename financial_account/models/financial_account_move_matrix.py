# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.addons.financial.constants import (
    FINANCIAL_DEBT_2PAY,
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_MONEY_IN,
    FINANCIAL_MONEY_OUT,
    FINANCIAL_PAYMENT,
    FINANCIAL_RECEIPT,
)


class FinancialAccountMoveMatrix(models.Model):

    _name = 'financial.account.move.matrix'
    _description = 'Financial Account Move Matrix'

    company_id = fields.Many2one(
        comodel_name='res.company',
        related='account_journal_id.company_id',
        store=True,
        readonly=True,
    )
    account_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        ondelete='restrict',
    )
    account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Account',
        index=True,
        required=True,
        domain=[('type', '=', 'A')],
    )
    document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Document type',
        ondelete='restrict',
        index=True,
    )
    account_move_template_2receive_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Receivable',
        ondelete='restrict',
    )
    account_move_template_receipt_item_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Receipt',
        ondelete='restrict',
    )
    account_move_template_money_in_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Money In',
        ondelete='restrict',
    )
    account_move_template_2pay_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Payable',
        ondelete='restrict',
    )
    account_move_template_payment_item_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Payment',
        ondelete='restrict',
    )
    account_move_template_money_out_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Money out',
        ondelete='restrict',
    )

    _sql_constraints = [(
        'matrix_company_type_uniq',
        'unique(account_id, document_type_id, company_id)',
        "'Financial move templates bust be unique per document type and "
        "company!")]

    @api.multi
    def map_account_matrix_id(self, **kwargs):

        matrix_id = self.env['financial.account.move.matrix']
        account_id = kwargs.get('account_id', False)
        document_type_id = kwargs.get('document_type_id', False)

        if account_id and document_type_id:
            matrix_id = self.search([
                ('document_type_id', '=', document_type_id),
                ('account_id', '=', account_id)
            ], limit=1)

        if account_id and not matrix_id:
            matrix_id = self.search([
                ('account_id', '=', account_id)
            ], limit=1)

        return matrix_id

    @api.multi
    def map_account_move_template_id(self, **kwargs):

        move_template = self.env['financial.account.move.template']

        matrix_id = kwargs.get('matrix_id', False)
        type = kwargs.get('type', False)

        if matrix_id and type:
            matrix = self.env[
                'financial.account.move.matrix'].browse(matrix_id)

            if type == FINANCIAL_DEBT_2RECEIVE and \
                    matrix.account_move_template_2receive_id:
                move_template = matrix.account_move_template_2receive_id

            elif type == FINANCIAL_DEBT_2PAY and \
                    matrix.account_move_template_2pay_id:
                move_template = matrix.account_move_template_2pay_id

            elif type == FINANCIAL_RECEIPT and \
                    matrix.account_move_template_receipt_item_id:
                move_template = matrix.account_move_template_receipt_item_id

            elif type == FINANCIAL_PAYMENT and \
                    matrix.account_move_template_payment_item_id:
                move_template = matrix.account_move_template_payment_item_id

            elif type == FINANCIAL_MONEY_IN and \
                    matrix.account_move_template_money_in_id:
                move_template = matrix.account_move_template_money_in_id

            elif type == FINANCIAL_MONEY_OUT and \
                    matrix.account_move_template_money_out_id:
                move_template = matrix.account_move_template_money_out_id

        return move_template
