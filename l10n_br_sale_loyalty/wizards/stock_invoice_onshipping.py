# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, models


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    def _create_invoice(self, invoice_values):
        """Fold the loyalty reward lines of the related sale order(s) into the
        fiscal values (vDesc, vFrete...) of the invoice product lines before
        the invoice is created, so a single valid invoice is issued from the
        delivery and its total matches what the customer actually paid.
        """
        self._fold_loyalty_rewards(invoice_values)
        return super()._create_invoice(invoice_values)

    @staticmethod
    def _loyalty_x2m_ids(command_list):
        """Extract the record ids targeted by a x2many command list."""
        ids = []
        for command in command_list or []:
            if not isinstance(command, list | tuple) or not command:
                continue
            code = command[0]
            if code in (Command.SET, Command.LINK) and len(command) > 2:
                ids.extend(command[2] if code == Command.SET else [command[1]])
            elif code == Command.LINK:
                ids.append(command[1])
        return ids

    def _fold_loyalty_rewards(self, invoice_values):
        line_vals = [
            command[2]
            for command in invoice_values.get("invoice_line_ids") or []
            if isinstance(command, list | tuple)
            and command
            and command[0] == Command.CREATE
            and command[2]
        ]
        sale_line_obj = self.env["sale.order.line"]
        vals_by_sale_line = {}
        orders = self.env["sale.order"]
        for vals in line_vals:
            sale_line_ids = self._loyalty_x2m_ids(vals.get("sale_line_ids"))
            for sale_line in sale_line_obj.browse(sale_line_ids):
                vals_by_sale_line.setdefault(sale_line, []).append(vals)
                orders |= sale_line.order_id
        if not orders:
            return
        reward_lines = orders.order_line.filtered(
            lambda ln: ln.is_reward_line and ln._loyalty_folds_into_invoice()
        )
        for reward in reward_lines:
            targets = [
                vals
                for sale_line in reward.reward_discounted_line_ids
                for vals in vals_by_sale_line.get(sale_line, [])
            ]
            if targets:
                self._loyalty_apply_fold(reward, targets)

    def _loyalty_fold_weights(self, targets, fname):
        """Weights to distribute a folded reward amount over the target invoice
        line values. Defaults to the line amount; a reward that lowers a field
        the lines already carry (e.g. a free-shipping reward lowering
        ``freight_value``) is better distributed by that field, so it zeroes
        out exactly. Extended by modules handling other reward types.
        """
        return [
            abs((vals.get("price_unit") or 0.0) * (vals.get("quantity") or 0.0))
            for vals in targets
        ]

    def _loyalty_apply_fold(self, reward, targets):
        folds = reward._loyalty_reward_fiscal_fold()
        if not folds:
            return
        currency = reward.currency_id
        for fname, total in folds.items():
            if not total:
                continue
            weights = self._loyalty_fold_weights(targets, fname)
            total_weight = sum(weights)
            if total_weight:
                shares = [
                    currency.round(total * weight / total_weight) for weight in weights
                ]
            else:
                even = currency.round(total / len(targets))
                shares = [even] * len(targets)
            # Rounding remainder goes to the last target line.
            shares[-1] = currency.round(total - sum(shares[:-1]))
            for vals, share in zip(targets, shares, strict=False):
                vals[fname] = (vals.get(fname) or 0.0) + share
