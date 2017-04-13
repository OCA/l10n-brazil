# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import fields, models


class ResCurrency(models.Model):
    _name = 'res.currency'
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
