# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError


class PosSession(models.Model):

    _inherit = "pos.session"

    def _check_invoices_are_posted(self):
        """The method was override due to the lack of the cancellation flow
        in the original method and that it does not take into account.move the
        change of the invoice state from 'posted' to 'cancel'.
        """
        unposted_invoices = self.order_ids.account_move.filtered(
            lambda x: x.state not in ["posted", "cancel"]
        )
        if unposted_invoices:
            raise UserError(
                _(
                    "You cannot close the POS when invoices are not posted or cancelled.\n"
                    "Invoices: %s"
                )
                % str.join(
                    "\n",
                    [
                        "%s - %s" % (invoice.name, invoice.state)
                        for invoice in unposted_invoices
                    ],
                )
            )

    # flake8: noqa: C901
    def _accumulate_amounts(self, data):
        """It was necessary to overwrite the method due to the necessary
        condition to prevent invoices related to orders in the "cancelled"
        state from entering the reconciliation process and preventing the
        session from being closed.
        """
        amounts = lambda: {"amount": 0.0, "amount_converted": 0.0}  # noqa: E731
        tax_amounts = lambda: {  # noqa: E731
            "amount": 0.0,
            "amount_converted": 0.0,
            "base_amount": 0.0,
            "base_amount_converted": 0.0,
        }
        split_receivables = defaultdict(amounts)
        split_receivables_cash = defaultdict(amounts)
        combine_receivables = defaultdict(amounts)
        combine_receivables_cash = defaultdict(amounts)
        invoice_receivables = defaultdict(amounts)
        sales = defaultdict(amounts)
        taxes = defaultdict(tax_amounts)
        stock_expense = defaultdict(amounts)
        stock_return = defaultdict(amounts)
        stock_output = defaultdict(amounts)
        rounding_difference = {"amount": 0.0, "amount_converted": 0.0}

        order_account_move_receivable_lines = defaultdict(
            lambda: self.env["account.move.line"]
        )
        rounded_globally = (
            self.company_id.tax_calculation_rounding_method == "round_globally"
        )
        for order in self.order_ids:
            if order.state != "cancel":
                for payment in order.payment_ids:
                    amount, date = payment.amount, payment.payment_date
                    if payment.payment_method_id.split_transactions:
                        if payment.payment_method_id.is_cash_count:
                            split_receivables_cash[payment] = self._update_amounts(
                                split_receivables_cash[payment],
                                {"amount": amount},
                                date,
                            )
                        else:
                            split_receivables[payment] = self._update_amounts(
                                split_receivables[payment], {"amount": amount}, date
                            )
                    else:
                        key = payment.payment_method_id
                        if payment.payment_method_id.is_cash_count:
                            combine_receivables_cash[key] = self._update_amounts(
                                combine_receivables_cash[key], {"amount": amount}, date
                            )
                        else:
                            combine_receivables[key] = self._update_amounts(
                                combine_receivables[key], {"amount": amount}, date
                            )

                if order.is_invoiced:
                    key = order.partner_id
                    if self.config_id.cash_rounding:
                        invoice_receivables[key] = self._update_amounts(
                            invoice_receivables[key],
                            {"amount": order.amount_paid},
                            order.date_order,
                        )
                    else:
                        invoice_receivables[key] = self._update_amounts(
                            invoice_receivables[key],
                            {"amount": order.amount_total},
                            order.date_order,
                        )
                    for move_line in order.account_move.line_ids.filtered(
                        lambda aml: aml.account_id.internal_type == "receivable"
                        and not aml.reconciled
                    ):
                        key = (
                            order.partner_id.commercial_partner_id.id,
                            move_line.account_id.id,
                        )
                        order_account_move_receivable_lines[key] |= move_line
                else:
                    order_taxes = defaultdict(tax_amounts)
                    for order_line in order.lines:
                        line = self._prepare_line(order_line)
                        sale_key = (
                            line["income_account_id"],
                            -1 if line["amount"] < 0 else 1,
                            tuple(
                                (
                                    tax["id"],
                                    tax["account_id"],
                                    tax["tax_repartition_line_id"],
                                )
                                for tax in line["taxes"]
                            ),
                            line["base_tags"],
                        )
                        sales[sale_key] = self._update_amounts(
                            sales[sale_key],
                            {"amount": line["amount"]},
                            line["date_order"],
                        )
                        for tax in line["taxes"]:
                            tax_key = (
                                tax["account_id"] or line["income_account_id"],
                                tax["tax_repartition_line_id"],
                                tax["id"],
                                tuple(tax["tag_ids"]),
                            )
                            order_taxes[tax_key] = self._update_amounts(
                                order_taxes[tax_key],
                                {"amount": tax["amount"], "base_amount": tax["base"]},
                                tax["date_order"],
                                round=not rounded_globally,
                            )
                    for tax_key, amounts in order_taxes.items():
                        if rounded_globally:
                            amounts = self._round_amounts(amounts)
                        for amount_key, amount in amounts.items():
                            taxes[tax_key][amount_key] += amount

                    if self.company_id.anglo_saxon_accounting and order.picking_ids.ids:
                        stock_moves = (
                            self.env["stock.move"]
                            .sudo()
                            .search(
                                [
                                    ("picking_id", "in", order.picking_ids.ids),
                                    ("company_id.anglo_saxon_accounting", "=", True),
                                    (
                                        "product_id.categ_id.property_valuation",
                                        "=",
                                        "real_time",
                                    ),
                                ]
                            )
                        )
                        for move in stock_moves:
                            exp_key = move.product_id._get_product_accounts()["expense"]
                            out_key = (
                                move.product_id.categ_id.property_stock_account_output_categ_id
                            )
                            amount = -sum(
                                move.sudo().stock_valuation_layer_ids.mapped("value")
                            )
                            stock_expense[exp_key] = self._update_amounts(
                                stock_expense[exp_key],
                                {"amount": amount},
                                move.picking_id.date,
                                force_company_currency=True,
                            )
                            if move.location_id.usage == "customer":
                                stock_return[out_key] = self._update_amounts(
                                    stock_return[out_key],
                                    {"amount": amount},
                                    move.picking_id.date,
                                    force_company_currency=True,
                                )
                            else:
                                stock_output[out_key] = self._update_amounts(
                                    stock_output[out_key],
                                    {"amount": amount},
                                    move.picking_id.date,
                                    force_company_currency=True,
                                )

                    if self.config_id.cash_rounding:
                        diff = order.amount_paid - order.amount_total
                        rounding_difference = self._update_amounts(
                            rounding_difference, {"amount": diff}, order.date_order
                        )

                    partners = order.partner_id | order.partner_id.commercial_partner_id
                    partners._increase_rank("customer_rank")

        if self.company_id.anglo_saxon_accounting:
            global_session_pickings = self.picking_ids.filtered(
                lambda p: not p.pos_order_id
            )
            if global_session_pickings:
                stock_moves = (
                    self.env["stock.move"]
                    .sudo()
                    .search(
                        [
                            ("picking_id", "in", global_session_pickings.ids),
                            ("company_id.anglo_saxon_accounting", "=", True),
                            (
                                "product_id.categ_id.property_valuation",
                                "=",
                                "real_time",
                            ),
                        ]
                    )
                )
                for move in stock_moves:
                    exp_key = move.product_id._get_product_accounts()["expense"]
                    out_key = (
                        move.product_id.categ_id.property_stock_account_output_categ_id
                    )
                    amount = -sum(move.stock_valuation_layer_ids.mapped("value"))
                    stock_expense[exp_key] = self._update_amounts(
                        stock_expense[exp_key],
                        {"amount": amount},
                        move.picking_id.date,
                        force_company_currency=True,
                    )
                    if move.location_id.usage == "customer":
                        stock_return[out_key] = self._update_amounts(
                            stock_return[out_key],
                            {"amount": amount},
                            move.picking_id.date,
                            force_company_currency=True,
                        )
                    else:
                        stock_output[out_key] = self._update_amounts(
                            stock_output[out_key],
                            {"amount": amount},
                            move.picking_id.date,
                            force_company_currency=True,
                        )
        MoveLine = self.env["account.move.line"].with_context(check_move_validity=False)

        data.update(
            {
                "taxes": taxes,
                "sales": sales,
                "stock_expense": stock_expense,
                "split_receivables": split_receivables,
                "combine_receivables": combine_receivables,
                "split_receivables_cash": split_receivables_cash,
                "combine_receivables_cash": combine_receivables_cash,
                "invoice_receivables": invoice_receivables,
                "stock_return": stock_return,
                "stock_output": stock_output,
                "order_account_move_receivable_lines": order_account_move_receivable_lines,
                "rounding_difference": rounding_difference,
                "MoveLine": MoveLine,
            }
        )
        return data
