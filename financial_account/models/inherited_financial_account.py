# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import fields, models


class FinancialAccount(models.Model):
    _inherit = b'financial.account'

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        ondelete='restrict',
    )
    account_matrix_ids = fields.One2many(
        comodel_name='financial.account.move.matrix',
        inverse_name='account_id',
        string='Accounting',
        ondelete='restrict',
    )
