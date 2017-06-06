# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models, api


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    name = fields.Char(
        string='Currency',
        size=70,
        required=True,
    )
    is_symbol = fields.Boolean(
        string='Is symbol?',
    )
    is_index = fields.Boolean(
        string='Is index?',
    )
    is_uom = fields.Boolean(
        string='Is UOM?',
    )
    is_currency = fields.Boolean(
        string='Is currency?',
        compute='_compute_is_currency',
        store=True,
    )

    @api.depends('is_symbol', 'is_index', 'is_uom')
    def _compute_is_currency(self):
        for currency in self:
            currency.is_currency = not (
                currency.is_symbol
                or currency.is_index
                or currency.is_uom
            )
