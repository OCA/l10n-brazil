# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools.float_utils import float_compare


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_net_cost_ratio(self, layers):
        """Net cost over gross price of the receipts behind ``layers``.

        Returns ``(net, gross)`` when every receipt was valued at the net
        cost, and None otherwise: a receipt the core priced itself (a return
        coming back, a company that did not opt in) is compared by the core,
        and a bill spread over both kinds cannot be put on a single basis.
        """
        self.ensure_one()
        precision = self.env["decimal.precision"].precision_get("Product Price")
        receipts = layers.filtered(
            lambda layer: layer.stock_move_id and layer.stock_move_id._is_in()
        )
        net = gross = 0.0
        for layer in receipts:
            move = layer.stock_move_id
            if (
                not move.valuation_via_stock_price
                or move.origin_returned_move_id
                or float_compare(
                    layer.unit_cost, move.cost_unit, precision_digits=precision
                )
            ):
                return None
            net += move.cost_unit * layer.quantity
            gross += move.price_unit * layer.quantity
        if not gross or float_compare(net, gross, precision_digits=precision) == 0:
            return None
        return net, gross

    def _generate_price_difference_vals(self, layers):
        """Compare the bill with the receipt on the same, net, basis.

        The core measures the price difference as the gross unit price of
        the bill minus the unit cost of the layer. A layer valued at the net
        cost lacks the recoverable taxes on purpose, so the core reads them
        as a price difference and puts them back into stock. The bill is
        brought to the net basis with the share of the gross price that the
        net cost kept, so a bill at the order price corrects nothing and a
        different price corrects the difference net of its own taxes.
        """
        ratio = self._get_net_cost_ratio(layers)
        if not ratio:
            return super()._generate_price_difference_vals(layers)
        line = self.with_context(l10n_br_net_cost_ratio=ratio)
        # The layers carry the context too: a refund reads the price of the
        # reversed bill line through them.
        return super(AccountMoveLine, line)._generate_price_difference_vals(
            layers.with_env(line.env)
        )

    def _get_gross_unit_price(self):
        price_unit = super()._get_gross_unit_price()
        ratio = self.env.context.get("l10n_br_net_cost_ratio")
        if ratio:
            net, gross = ratio
            price_unit = price_unit * net / gross
        return price_unit
