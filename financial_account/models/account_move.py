# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class AccountMove(models.Model):

    _inherit = 'account.move'

    financial_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='move_id',
        string='Financial Items',
        readonly=True,
        copy=False,
    )

    @api.multi
    def filter_financial_integration(self):
        return self.filtered(lambda m: m.journal_id.financial_integration)

    @api.multi
    def action_sync_account_with_financial(self):
        financial_move = self.env['financial.move']
        financial_move.sync_financial_account(self)

    @api.multi
    def assert_balanced(self):
        res = super(AccountMove, self).assert_balanced()
        if res:
            financial_to_sync = self.filter_financial_integration()
            financial_to_sync.action_sync_account_with_financial()
        return res

    @api.multi
    def post(self):
        with_financial = self.filtered(lambda m: m.financial_ids)
        with_financial.financial_ids._confirm()
        res = super(AccountMove, self).post()
        return res

    def _cancel_financial(self):
        self.financial_ids.action_cancel(
            _(u'Linked document canceled')
        )

    @api.multi
    def button_cancel(self):
        self._cancel_financial()
        return super(AccountMove, self).button_cancel()

    def unlink(self):
        self.financial_ids.unlink()
        return super(AccountMove, self).button_cancel()


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    financial_move_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='financial_account_move_line_id',
        string=u'Financial Moves',
        copy=False,
    )
