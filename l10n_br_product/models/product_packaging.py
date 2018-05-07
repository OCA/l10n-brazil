# -*- coding: utf-8 -*-
# @ 2018 KMEE INFORMATICA LTDA - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division, print_function, unicode_literals

from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    name = fields.Char(
        string='Espécie/embalagem'
    )
    qty = fields.Float(
        string='Quantidade por espécie/embalagem'
    )
