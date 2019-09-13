# -*- coding: utf-8 -*-
# Copyright (C) 2014  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    @api.model
    def _get_stock_move_values(self):
        vals = super(ProcurementOrder, self)._get_stock_move_values()
        if self.sale_line_id:
            vals.update({
                'fiscal_category_id':
                    self.sale_line_id.fiscal_category_id.id,
                'fiscal_position_id': self.sale_line_id.fiscal_position_id.id,
            })

        return vals
