# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons import decimal_precision as dp


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    @api.multi
    def _add_delivery_cost_to_so(self):
        self.ensure_one()
        sale_order = self.sale_id
        sale_order._compute_freight_distribution()
