# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _


class FinancialAccount(models.Model):
    _inherit = b'financial.account'

    account_move_template_2receive_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Account Move Template when Receivable',
        ondelete='restrict',
    )
    account_move_template_2pay_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Account Move Template when Payable',
        ondelete='restrict',
    )
    account_move_template_receipt_item_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Account Move Template when Receipt Item',
        ondelete='restrict',
    )
    account_move_template_payment_item_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Account Move Template when Payment Item',
        ondelete='restrict',
    )
    account_move_template_money_in_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Account Move Template when Money In',
        ondelete='restrict',
    )
    account_move_template_money_out_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Account Move Template when Money Out',
        ondelete='restrict',
    )
    account_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        ondelete='restrict',
    )
