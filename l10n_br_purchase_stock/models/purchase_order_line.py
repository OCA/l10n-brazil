# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    stock_price_br = fields.Monetary(
        string="Stock Price", compute="_compute_stock_price_br"
    )

    @api.depends("amount_total", "fiscal_tax_ids")
    def _compute_stock_price_br(self):
        for record in self:
            record.stock_price_br = 0

            if record.fiscal_operation_line_id:
                non_creditable_taxes = (
                    record.fiscal_operation_line_id.non_creditable_tax_definition_ids
                )
                price = record.amount_total

                for tax in record.fiscal_tax_ids:
                    if hasattr(record, "%s_tax_id" % (tax.tax_domain,)):
                        tax_id = getattr(record, "%s_tax_id" % (tax.tax_domain,))
                        if tax_id.tax_group_id not in non_creditable_taxes:
                            if not hasattr(record, "%s_value" % (tax.tax_domain)):
                                continue
                            price -= getattr(record, "%s_value" % (tax.tax_domain))

                price_precision = self.env["decimal.precision"].precision_get(
                    "Product Price"
                )
                record.stock_price_br = float_round(
                    (price / record.product_uom_qty), precision_digits=price_precision
                )

    def _prepare_stock_moves(self, picking):
        """Prepare the stock moves data for one order line.
        This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        values = super()._prepare_stock_moves(picking)
        for v in values:
            v.update(self._prepare_br_fiscal_dict())
            if self.env.company.purchase_create_invoice_policy == "stock_picking":
                v["invoice_state"] = "2binvoiced"
        return values

    @api.model
    def _prepare_purchase_order_line_from_procurement(
        self, product_id, product_qty, product_uom, company_id, values, po
    ):
        res = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values, po
        )
        if values.get("move_dest_ids"):
            for move in values.get("move_dest_ids"):
                move.fiscal_operation_id = (
                    move.fiscal_operation_id.inverse_fiscal_operation_id.id
                )

        return res
