# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange("requisition_id")
    def _onchange_requisition_id(self):
        res = super()._onchange_requisition_id()
        if self.company_id.country_id.code == "BR":
            if self.fiscal_operation_id:
                self._onchange_fiscal_operation_id()
                for line in self.order_line:
                    if not line.fiscal_operation_id:
                        line.fiscal_operation_id = self.fiscal_operation_id
                        line._onchange_fiscal_tax_ids()
        return res

    @api.onchange("partner_id", "company_id")
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if self.company_id.country_id.code == "BR":
            if self.fiscal_operation_id:
                self._onchange_fiscal_operation_id()
                for line in self.order_line:
                    if not line.fiscal_operation_id:
                        line.fiscal_operation_id = self.fiscal_operation_id
                    line._onchange_fiscal_tax_ids()
        return res
