# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    @api.onchange("partner_id", "company_id")
    def onchange_partner_id(self):
        super().onchange_partner_id()
        if self.company_id.country_id.code == "BR":
            if not self.requisition_id:
                return
            self._onchange_fiscal_operation_id()
            for line in self.order_line:
                line._onchange_fiscal_operation_id()
