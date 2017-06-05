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

    brazil_line_ids = fields.One2many(
        comodel_name='purchase.order.line.brazil',
        inverse_name='order_id',
        string='Linhas',
    )

    def _get_date(self):
        """
        Return the document date
        Used in _amount_all_wrapper
        """
        return self.date_order

    @api.one
    @api.depends('order_line.price_total')
    def _amount_all(self):
        if not self.is_brazilian:
            return super(PurchaseOrder, self)._amount_all()
        return self._amount_all_brazil()
