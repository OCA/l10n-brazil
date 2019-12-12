# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        values,
        group_id,
    ):
        """
         Returns a dictionary of values that will be used to create
          a stock move from a procurement.
        This function assumes that the given procurement has a
         rule (action == 'move') set on it.

        :param procurement: browse record
        :rtype: dictionary
        """
        values = super(ProcurementGroup, self)._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            values,
            group_id,
        )

        if self.purchase_line_id:
            values.update(
                {
                    "opeation_id": self.purchase_line_id.operation_id.id,
                    "operation_line_id": self.purchase_line_id.operation_line_id.id,
                }
            )

        return vals
