# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    def make_purchase_order(self):
        res = super().make_purchase_order()
        purchases = self.env["purchase.order"].search(res.get("domain"))
        for purchase in purchases:
            if purchase.fiscal_operation_id:
                purchase._onchange_partner_id_fiscal()
                for line in purchase.order_line:
                    description = line.name
                    price_unit = line.price_unit
                    line._onchange_product_id_fiscal()
                    line._onchange_fiscal_tax_ids()
                    line.name = description
                    for item in self.item_ids:
                        if item.keep_estimated_cost:
                            line.price_unit = price_unit
                            line.fiscal_price = price_unit
                            line._compute_amount()
        return res
