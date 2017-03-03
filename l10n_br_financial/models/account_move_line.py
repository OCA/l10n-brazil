# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

FINANCIAL_TYPE_AML = {
    'receivable': {
        'debit': 'r',
        'credit': 'rr',
    },
    'payable': {
        'credit': 'p',
        'debit': 'rr',
    }
}


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    financial_move_id = fields.Many2one(
        comodel_name='financial.move',
    )

    def _prepare_financial_move(self):
        type_move = FINANCIAL_TYPE_AML[self.account_id.internal_type]
        type_move = (
            self.credit and type_move['credit'] or
            self.debit and type_move['debit']
        )

        return dict(
            due_date=self.date_maturity,
            company_id=(self.company_id and self.company_id.id or
                        self.account_id.company_id and
                        self.account_id.company_id.id),
            currency_id=(self.currency_id and self.currency_id.id or
                         self.move_id.currency_id and
                         self.move_id.currency_id.id),
            amount_document=self.debit or self.credit,
            partner_id=self.partner_id and self.partner_id.id or False,
            document_date=self.date_maturity,
            document_number='1111',
            move_type=type_move,
            move_id=self.move_id and self.move_id.id,
            account_move_line_id=self.id,
        )

    @api.multi
    def sync_financeiro_lancamento_from_aml(self):
        # Se existir um financial que já tenha uma aml, atualizar o mesmo

        # self, date_maturity, partner_id, internal_type,
        # company_id, currency_id, debit = 0, credit = 0, ** kwargs):

        financial_obj = self.env['financial.move'].create(
            self._prepare_financial_move())
        financial_obj.action_confirm()
        return True

    def create(self, values):
        res = super(AccountMoveLine, self).create(values)
        if res and res.account_id.internal_type in ('receivable', 'payable'):
            res.sync_financeiro_lancamento_from_aml()
        return res

    def write(self, values):
        res = super(AccountMoveLine, self).write(values)
        # compute and inverse
        return res
