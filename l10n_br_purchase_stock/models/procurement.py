# -*- coding: utf-8 -*-
# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _get_stock_move_values(self):
        '''
         Returns a dictionary of values that will be used to create
          a stock move from a procurement.
        This function assumes that the given procurement has a
         rule (action == 'move') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        vals = super(ProcurementOrder, self)._get_stock_move_values()
        if self.purchase_line_id:
            vals.update({
                'fiscal_category_id':
                    self.purchase_line_id.fiscal_category_id.id,
                'fiscal_position_id':
                    self.purchase_line_id.fiscal_position_id.id,
            })

        return vals
