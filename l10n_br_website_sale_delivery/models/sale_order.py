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

    def _get_website_fiscal_freight(self):
        self.ensure_one()
        if not self.website_id or self.company_id.country_id.code != "BR":
            return 0.0
        fiscal_lines = self._get_non_delivery_lines().filtered("fiscal_operation_id")
        return sum(fiscal_lines.mapped("freight_value"))

    def _compute_amount_total_without_delivery(self):
        return (
            super()._compute_amount_total_without_delivery()
            - self._get_website_fiscal_freight()
        )

    def _get_amount_total_excluding_delivery(self):
        if (
            self.website_id
            and self.company_id.country_id.code == "BR"
            and self.fiscal_operation_id
        ):
            # Use the fiscal order total, which includes the freight distributed
            # across product lines, as the basis for express checkout.
            return self._compute_amount_total_without_delivery()
        return super()._get_amount_total_excluding_delivery()

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
