# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Inverse of sale_loyalty_order_line_link's reward_line_ids: the regular
    # order lines whose fiscal discount (vDesc) carries this reward line.
    reward_discounted_line_ids = fields.Many2many(
        comodel_name="sale.order.line",
        relation="sale_line_reward_line_rel",
        column1="reward_line_id",
        column2="sale_line_id",
        string="Discounted lines",
        help="Regular order lines whose fiscal discount carries this reward "
        "line when the invoice is generated from the delivery.",
    )

    # A folded reward line's qty_invoiced is computed from the qty_invoiced of
    # the lines it discounts (same field, other records), so the dependency is
    # self-referential and the field must be flagged recursive.
    qty_invoiced = fields.Float(recursive=True)

    def _loyalty_reward_fiscal_fold(self):
        """Fiscal amounts a reward line contributes to the invoice product
        lines it applies to, as ``{fiscal_field: amount_to_distribute}``.

        A discount reward lowers the fiscal discount (``discount_value`` /
        vDesc). Other modules extend this (e.g. l10n_br_sale_loyalty_delivery
        folds a free-shipping reward into ``freight_value`` / vFrete). An empty
        result means the reward is invoiced the regular way.
        """
        self.ensure_one()
        if not self.is_reward_line:
            return {}
        if self.reward_id.reward_type == "discount":
            return {"discount_value": abs(self.price_subtotal)}
        return {}

    def _loyalty_folds_into_invoice(self):
        """A reward line whose value is folded into the fiscal values of the
        lines it applies to, instead of being invoiced as a separate (negative)
        line. Such a line is never invoiced on its own: it has no stock move, so
        the picking-based invoice would drop it and leave the invoice partially
        paid, and a negative line is not a valid NF-e item.
        """
        self.ensure_one()
        return bool(self._loyalty_reward_fiscal_fold()) and bool(
            self.reward_discounted_line_ids
        )

    @api.depends(
        "reward_discounted_line_ids.qty_invoiced",
        "reward_discounted_line_ids.product_uom_qty",
    )
    def _compute_qty_invoiced(self):
        """Folded reward lines carry no invoice line of their own, so the core
        computation leaves them at 0 and the order would stay 'to invoice'
        (and its invoice button would emit the discount as a second document).
        Mirror the invoiced ratio of the lines the reward discounts instead.
        """
        res = super()._compute_qty_invoiced()
        for line in self:
            if not line._loyalty_folds_into_invoice():
                continue
            sources = line.reward_discounted_line_ids
            ordered = sum(sources.mapped("product_uom_qty"))
            invoiced = sum(sources.mapped("qty_invoiced"))
            ratio = (invoiced / ordered) if ordered else 0.0
            line.qty_invoiced = line.product_uom_qty * ratio
        return res
