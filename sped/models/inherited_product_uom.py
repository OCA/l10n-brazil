# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import fields, models


class ProductUoM(models.Model):
    _name = 'product.uom'
    _inherit = 'product.uom'

    sped_unidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string=u'Unidade',
    )
