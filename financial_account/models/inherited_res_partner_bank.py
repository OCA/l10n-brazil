# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import fields, models


class ResPartnerBank(models.Model):
    _inherit = b'res.partner.bank'

    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        ondelete='restrict',
    )
