# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    account_id = fields.Many2one(
        required=False,
    )
