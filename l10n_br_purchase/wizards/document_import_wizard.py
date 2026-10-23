# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class DocumentImportWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.import.wizard"

    def _xped_from_file(self):
        """Return (xPed, nItemPed) for each NF-e line. Empty for other XML."""
        if not self.file:
            return []
        try:
            binding = self._parse_file()
        except Exception:
            _logger.debug("Imported file has no NF-e lines to match a purchase order")
            return []
        inf = getattr(binding, "infNFe", None)
        nested = getattr(binding, "NFe", None)
        if inf is None and nested is not None:
            inf = getattr(nested, "infNFe", None)
        if inf is None:
            return []
        rows = []
        for det in getattr(inf, "det", []) or []:
            prod = getattr(det, "prod", None)
            if prod is None:
                continue
            rows.append(
                (
                    (getattr(prod, "xPed", None) or "").strip(),
                    (getattr(prod, "nItemPed", None) or "").strip(),
                )
            )
        return rows

    def _get_xml_line_previews(self):
        previews = super()._get_xml_line_previews()
        orders = self._xped_from_file()
        for index, preview in enumerate(previews):
            if index >= len(orders):
                break
            preview["partner_order"], preview["partner_order_line"] = orders[index]
        return previews

    def _referenced_purchase_orders(self):
        orders = self.env["purchase.order"]
        refs = [order for order, _item in self._xped_from_file() if order]
        refs += [
            line.partner_order for line in self.match_line_ids if line.partner_order
        ]
        refs = list(dict.fromkeys(refs))
        partner_ids = self._issuer_partner_ids()
        if not refs or not partner_ids or not self.company_id:
            return orders
        lines = self.env["purchase.order.line"].search(
            [
                ("partner_order", "in", refs),
                ("order_id.company_id", "=", self.company_id.id),
                ("order_id.state", "in", ("purchase", "done")),
                ("order_id.partner_id", "in", partner_ids),
            ]
        )
        orders = lines.order_id
        orders |= self.env["purchase.order"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("state", "in", ("purchase", "done")),
                ("partner_id", "in", partner_ids),
                "|",
                ("name", "in", refs),
                ("partner_ref", "in", refs),
            ]
        )
        return orders

    def _is_strong_move_match(self, move):
        if super()._is_strong_move_match(move):
            return True
        orders = self._referenced_purchase_orders()
        if len(orders) != 1:
            return False
        bills = orders.invoice_ids.filtered(
            lambda bill: bill.state == "draft"
            and bill.move_type == "in_invoice"
            and bill.company_id == self.company_id
        )
        return len(bills) == 1 and move == bills

    def _match_purchase_line(self, fiscal_line, partner):
        """Return the single open purchase line for this fiscal line."""
        purchase_lines = self.env["purchase.order.line"]
        if not partner or not fiscal_line.company_id:
            return purchase_lines
        partner_ids = partner.commercial_partner_id.ids
        child_ids = partner.commercial_partner_id.child_ids.ids
        domain = [
            ("order_id.partner_id", "in", partner_ids + child_ids + partner.ids),
            ("order_id.state", "in", ("purchase", "done")),
            ("order_id.company_id", "=", fiscal_line.company_id.id),
        ]
        order = (fiscal_line.partner_order or "").strip()
        item = (fiscal_line.partner_order_line or "").strip()
        if order and "partner_order" in purchase_lines._fields:
            by_order = purchase_lines.search(domain + [("partner_order", "=", order)])
            if item:
                exact = by_order.filtered(
                    lambda line: (line.partner_order_line or "").strip() == item
                )
                if len(exact) == 1:
                    return exact
                if len(exact) > 1:
                    return purchase_lines
            open_lines = by_order.filtered("qty_to_invoice")
            if len(open_lines) == 1:
                return open_lines
            if len(by_order) == 1:
                return by_order
            if order:
                return purchase_lines
        if not fiscal_line.product_id:
            return purchase_lines
        by_product = purchase_lines.search(
            domain + [("product_id", "=", fiscal_line.product_id.id)]
        )
        open_lines = by_product.filtered("qty_to_invoice")
        if len(open_lines) == 1:
            return open_lines
        return purchase_lines

    def _link_purchase_order_lines(self, move, fiscal_document):
        for fiscal_line in fiscal_document.fiscal_line_ids:
            invoice_line = move.invoice_line_ids.filtered(
                lambda line, fiscal_line=fiscal_line: line.fiscal_document_line_id
                == fiscal_line
            )[:1]
            if not invoice_line or invoice_line.purchase_line_id:
                continue
            purchase_line = self._match_purchase_line(fiscal_line, move.partner_id)
            if purchase_line:
                invoice_line.purchase_line_id = purchase_line
        return move
