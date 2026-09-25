# Copyright (C) 2020  Magno Costa - Akretion
# Copyright (C) 2020  Renato Lima - Akretion
# Copyright (C) 2026 - Madooit
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_update_po_from_nfe(self):
        self.ensure_one()
        wizard_model = self.env["purchase.update.from.nfe.wizard"]
        vals = wizard_model._get_wizard_vals_from_move(self)
        if not vals.get("line_ids"):
            raise UserError(
                _("No matching purchase order line found for the imported document.")
            )
        wizard = wizard_model.create(vals)
        return {
            "name": _("Update PO from NFe"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.update.from.nfe.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }

    def action_create_po_from_nfe(self):
        self.ensure_one()
        if self.move_type != "in_invoice":
            raise UserError(
                _("A purchase order can only be created from a vendor bill.")
            )
        if not self.fiscal_document_id:
            raise UserError(_("The vendor bill has no imported fiscal document."))
        po = self.env["purchase.order"].create(self._prepare_po_from_nfe_vals())
        for po_line in po.order_line:
            po_line._onchange_fiscal_tax_ids()
            po_line._compute_tax_fields()
            po_line._compute_amount()
        return {
            "name": _("Purchase Order"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": po.id,
        }

    def _prepare_po_from_nfe_vals(self):
        self.ensure_one()
        fiscal_doc = self.fiscal_document_id
        order_lines = []
        for bill_line in self.invoice_line_ids.filtered("product_id"):
            line_vals = self._prepare_po_line_from_nfe_vals(bill_line)
            if line_vals:
                order_lines.append((0, 0, line_vals))
        return {
            "partner_id": self.partner_id.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "date_order": fiscal_doc.document_date or self.invoice_date,
            "partner_ref": fiscal_doc.document_key
            or (f"{fiscal_doc.document_serie} / {fiscal_doc.document_number}"),
            "fiscal_operation_id": (
                fiscal_doc.fiscal_operation_id or self.fiscal_operation_id
            ).id,
            "order_line": order_lines,
        }

    def _prepare_po_line_from_nfe_vals(self, bill_line):
        self.ensure_one()
        product = bill_line.product_id
        if not product:
            return {}
        product_uom = product.uom_po_id or product.uom_id
        uom = bill_line.uom_id or bill_line.product_uom_id
        quantity = bill_line.quantity
        price_unit = bill_line.price_unit
        if uom and product_uom and uom != product_uom:
            factor = uom._compute_quantity(1.0, product_uom)
            quantity = bill_line.quantity * factor
            price_unit = bill_line.price_unit * factor
        fiscal_vals = bill_line.fiscal_document_line_id._prepare_br_fiscal_dict()
        for key in (
            "name",
            "product_id",
            "quantity",
            "uom_id",
            "fiscal_quantity",
            "taxes_id",
            "price_unit",
        ):
            fiscal_vals.pop(key, None)
        vals = {
            "name": bill_line.name,
            "product_id": product.id,
            "product_qty": quantity,
            "product_uom": product_uom.id,
            "price_unit": price_unit,
        }
        vals.update(fiscal_vals)
        return vals

    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):
        if self.purchase_id:
            if self.purchase_id.fiscal_operation_id:
                self.fiscal_operation_id = self.purchase_id.fiscal_operation_id
                if not self.document_type_id:
                    # Testes não passam por aqui, qual seria esse caso de uso?
                    # Porque se não houver o codigo pode ser removido
                    self.document_type_id = self.company_id.document_type_id
        return super()._onchange_purchase_auto_complete()
