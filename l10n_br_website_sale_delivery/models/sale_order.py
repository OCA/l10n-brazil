# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("amount_freight_value", "company_id.country_id")
    def _compute_amount_delivery(self):
        result = super()._compute_amount_delivery()
        for order in self:
            if order.company_id.country_id.code == "BR":
                order.amount_delivery = order.amount_freight_value
        return result

    @api.model_create_multi
    def create(self, vals_list):
        default_website = self.default_get(["website_id"]).get("website_id")
        vals_list = [
            dict(vals, force_compute_delivery_costs_by_total=True)
            if vals.get("website_id", default_website)
            else vals
            for vals in vals_list
        ]
        return super().create(vals_list)
