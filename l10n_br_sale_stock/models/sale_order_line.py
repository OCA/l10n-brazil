# Copyright (C) 2013  Raphaël Valyi - Akretion
# Copyright (C) 2014  Renato Lima - Akretion
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self, group_id=False):
        values = {}
        if self.order_id.fiscal_operation_id:
            values = self._prepare_br_fiscal_dict()
        values.update(super()._prepare_procurement_values(group_id))

        return values
