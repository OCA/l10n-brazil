# Copyright 2023 - TODAY, Marcel Savergnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class SaleBlanketOrderWizard(models.TransientModel):
    _inherit = ["sale.blanket.order.wizard"]

    def _prepare_so_line_vals(self, line):
        fiscal_vals = line.blanket_line_id._prepare_br_fiscal_dict()

        # change quantity
        fiscal_vals["quantity"] = line.qty
        fiscal_vals["fiscal_quantity"] = line.qty

        # set company
        fiscal_vals["company_id"] = self.blanket_order_id.company_id.id

        fiscal_vals = self._simulate_onchange_price_subtotal(fiscal_vals)

        vals = super()._prepare_so_line_vals(line=line)
        vals.update(fiscal_vals)
        return vals

    def _simulate_onchange_price_subtotal(self, values):
        """
        Simulate onchange price_subtotal
        :param values: dict
        :return: dict
        """
        line = self.env["account.move.line"].new(values.copy())
        line._onchange_price_subtotal()
        new_values = line._convert_to_write(line._cache)
        values.update(new_values)
        del values["move_id"]
        return values

    def _prepare_so_vals(
        self,
        customer,
        user_id,
        currency_id,
        pricelist_id,
        payment_term_id,
        order_lines_by_customer,
    ):
        vals = super()._prepare_so_vals(
            customer=customer,
            user_id=user_id,
            currency_id=currency_id,
            pricelist_id=pricelist_id,
            payment_term_id=payment_term_id,
            order_lines_by_customer=order_lines_by_customer,
        )

        fiscal_operation_ids = []
        blanket_order_line_ids = []
        for line in order_lines_by_customer[customer]:
            if isinstance(line[2], dict):
                if not fiscal_operation_ids:
                    fiscal_operation_ids.append(line[2]["fiscal_operation_id"])
                elif fiscal_operation_ids[0] != line[2]["fiscal_operation_id"]:
                    raise UserError(
                        _(
                            "Can not create Sale Order from Blanket "
                            "Order lines with different fiscal operations"
                        )
                    )
                blanket_order_line_ids.append(line[2]["blanket_order_line"])
        blanket_order_lines = self.env["sale.blanket.order.line"].search(
            [("id", "in", blanket_order_line_ids)]
        )
        default_blanket_order = blanket_order_lines[0].order_id
        if default_blanket_order:
            fiscal_vals = default_blanket_order._prepare_br_fiscal_dict()
            vals.update(fiscal_vals)
        return vals
