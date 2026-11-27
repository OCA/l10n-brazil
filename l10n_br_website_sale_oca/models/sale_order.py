# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _is_br_website_order(self):
        self.ensure_one()
        return self.website_id and self.company_id.country_id.code == "BR"

    def _update_address(self, partner_id, fnames=None):
        result = super()._update_address(partner_id, fnames)
        if fnames and self._is_br_website_order() and self.fiscal_operation_id:
            lines = self.order_line.filtered(
                lambda line: not (line.display_type or line.fiscal_operation_id)
            )
            lines.fiscal_operation_id = self.fiscal_operation_id
        return result

    def _prepare_order_line_values(self, product_id, quantity, **kwargs):
        values = super()._prepare_order_line_values(product_id, quantity, **kwargs)
        if (
            self._is_br_website_order()
            and self.fiscal_operation_id
            and not self._is_anonymous_cart()
        ):
            values.setdefault("fiscal_operation_id", self.fiscal_operation_id.id)
        return values
