# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    type = fields.Selection(selection_add=[('product', 'Stockable Product')])
