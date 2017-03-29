# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    financial_ids = fields.One2many(
        comodel_name='financial.move',
        related='move_id.financial_ids',
        string=u'Financial Items',
        readonly=True,
        copy=False
    )
