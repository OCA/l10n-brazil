# Copyright 2021 - TODAY, Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    @api.onchange("requisition_id", "partner_id")
    def _onchange_requisition_partner_id(self):
        if not self.requisition_id:
            return

        self.onchange_partner_id()
        self._onchange_fiscal_operation_id()
        for line in self.order_line:
            line.fiscal_operation_id = self.fiscal_operation_id
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_product_id_fiscal()
            line._onchange_fiscal_taxes()
            line.onchange_product_id()
