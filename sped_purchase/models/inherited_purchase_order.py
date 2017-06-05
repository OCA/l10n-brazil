# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)


class PurchaseOrder(SpedCalculoImposto, models.Model):
    _inherit = 'purchase.order'

    order_line_brazil_ids = fields.One2many(
        comodel_name='purchase.order.line.brazil',
        inverse_name='order_id',
        string='Linhas',
    )
