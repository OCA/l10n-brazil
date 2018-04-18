# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import fields, models


class ProductUom(models.Model):
    _inherit = 'product.uom'

    codigo = fields.Char(
        size=6,
    )
