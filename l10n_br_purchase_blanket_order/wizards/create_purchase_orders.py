# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError


class PurchaseBlanketOrderWizard(models.TransientModel):
    _inherit = "purchase.blanket.order.wizard"

    def _prepare_po_line_vals(self, line):
        fiscal_vals = line.blanket_line_id._prepare_br_fiscal_dict()

        if line.qty != fiscal_vals["quantity"]:
            # The tax/amount fields above were computed for the blanket
            # order line's original quantity. Changing the quantity on a
            # virtual record lets the ORM detect the change and recompute
            # them naturally, the same mechanism used by onchange.
            virtual = self.env["l10n_br_fiscal.document.line"].new(fiscal_vals)
            virtual.quantity = line.qty
            fiscal_vals = {
                fname: virtual._fields[fname].convert_to_write(virtual[fname], virtual)
                for fname in fiscal_vals
            }

        fiscal_vals["company_id"] = self.blanket_order_id.company_id.id

        fiscal_vals = self._simulate_onchange_price_subtotal(fiscal_vals)

        date_planned = line.blanket_line_id.date_schedule
        vals = {
            "product_id": line.product_id.id,
            "name": line.product_id.name,
            "date_planned": date_planned
            if date_planned
            else line.blanket_line_id.order_id.date_start,
            "product_uom": line.product_uom.id,
            "sequence": line.blanket_line_id.sequence,
            "price_unit": line.blanket_line_id.price_unit,
            "blanket_order_line": line.blanket_line_id.id,
            "product_qty": line.qty,
            "taxes_id": [(6, 0, line.taxes_id.ids)],
            **fiscal_vals,
        }
        # OCA copies taxes_id from the wizard related field (blanket taxes_id),
        # which may still be empty on BR CoA. Force account taxes from fiscal
        # after fiscal_vals so it is not overwritten.
        blanket_line = line.blanket_line_id
        if blanket_line.fiscal_operation_line_id:
            company = blanket_line.company_id or self.blanket_order_id.company_id
            vals["taxes_id"] = [
                (
                    6,
                    0,
                    blanket_line.fiscal_tax_ids.account_taxes(
                        user_type="purchase",
                        fiscal_operation=blanket_line.fiscal_operation_id,
                        company=company,
                    ).ids,
                )
            ]
        return vals

    def _simulate_onchange_price_subtotal(self, values):
        line = self.env["account.move.line"].new(values.copy())
        new_values = line._convert_to_write(line._cache)
        values.update(new_values)
        return values

    def _prepare_po_vals(self, supplier, currency_id, payment_term_id, order_lines):
        order_vals = {
            "partner_id": int(supplier),
            "currency_id": currency_id if currency_id else False,
            "payment_term_id": payment_term_id if payment_term_id else False,
            "order_line": order_lines,
        }

        if self.blanket_order_id:
            order_vals.update(
                {
                    "partner_ref": self.blanket_order_id.partner_ref,
                    "origin": self.blanket_order_id.name,
                }
            )

        fiscal_operation_ids = []
        blanket_order_line_ids = []
        for line in order_lines:
            if isinstance(line[2], dict):
                if not fiscal_operation_ids:
                    fiscal_operation_ids.append(line[2]["fiscal_operation_id"])
                elif fiscal_operation_ids[0] != line[2]["fiscal_operation_id"]:
                    raise UserError(
                        _(
                            "Can not create Purchase Order from Blanket "
                            "Order lines with different fiscal operations"
                        )
                    )
                blanket_order_line_ids.append(line[2]["blanket_order_line"])

        blanket_order_lines = self.env["purchase.blanket.order.line"].search(
            [("id", "in", blanket_order_line_ids)]
        )
        default_blanket_order = blanket_order_lines[:1].order_id
        if default_blanket_order:
            fiscal_vals = default_blanket_order._prepare_br_fiscal_dict()
            order_vals.update(fiscal_vals)

        return order_vals

    def create_purchase_order(self):
        order_lines_by_supplier = defaultdict(list)
        currency_id = 0
        payment_term_id = 0

        for line in self.line_ids:
            if line.qty == 0.0:
                continue

            if line.qty > line.remaining_uom_qty:
                raise UserError(_("You can't order more than the remaining quantities"))

            vals = self._prepare_po_line_vals(line)
            order_lines_by_supplier[line.partner_id.id].append((0, 0, vals))

            if currency_id == 0:
                currency_id = line.blanket_line_id.order_id.currency_id.id
            elif currency_id != line.blanket_line_id.order_id.currency_id.id:
                currency_id = False

            if payment_term_id == 0:
                payment_term_id = line.blanket_line_id.payment_term_id.id
            elif payment_term_id != line.blanket_line_id.payment_term_id.id:
                payment_term_id = False

        if not order_lines_by_supplier:
            raise UserError(_("An order can't be empty"))

        if not currency_id:
            raise UserError(
                _(
                    "Can not create Purchase Order from Blanket "
                    "Order lines with different currencies"
                )
            )

        res = []
        for supplier, order_lines in order_lines_by_supplier.items():
            order_vals = self._prepare_po_vals(
                supplier=supplier,
                currency_id=currency_id,
                payment_term_id=payment_term_id,
                order_lines=order_lines,
            )
            purchase_order = self.env["purchase.order"].create(order_vals)
            res.append(purchase_order.id)

        return {
            "domain": [("id", "in", res)],
            "name": _("RFQ"),
            "view_mode": "tree,form",
            "res_model": "purchase.order",
            "view_id": False,
            "context": {"from_purchase_order": True},
            "type": "ir.actions.act_window",
        }
