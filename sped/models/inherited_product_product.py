# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    sped_produto_id = fields.Many2one('sped.produto', 'Produto')
