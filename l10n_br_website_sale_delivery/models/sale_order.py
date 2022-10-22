# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends(
        "amount_freight_value",
        "order_line.price_unit",
        "order_line.tax_id",
        "order_line.discount",
        "order_line.product_uom_qty",
    )
    def _compute_amount_delivery(self):
        result = super()._compute_amount_delivery()

        for order in self:
            if order.company_id.country_id.code == "BR":
                if self.env.user.has_group(
                    "account.group_show_line_subtotals_tax_excluded"
                ):
                    order.amount_delivery = order.amount_freight_value
                else:
                    order.amount_delivery = order.amount_freight_value
        return result

    @api.model
    def create(self, values):
        if values.get("website_id"):
            values.update(force_compute_delivery_costs_by_total=True)
        return super().create(values)
