# Copyright (C) 2026 - Madooit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_TAX_ID_FIELDS

# Fiscal fields honored when pushing the NFe data back to the purchase order
# line: the tax mapping ids plus the CST/origin/base fields and the additional
# charges read from the imported document line.
_BILL_TO_PO_FISCAL_FIELDS = [
    "icms_base_type",
    "icms_cst_id",
    "icms_origin",
    "icmsst_base_type",
    "ipi_cst_id",
    "pis_cst_id",
    "cofins_cst_id",
    "discount_value",
    "freight_value",
    "insurance_value",
    "other_value",
] + list(FISCAL_TAX_ID_FIELDS)


class PurchaseUpdateFromNfeWizard(models.TransientModel):
    _name = "purchase.update.from.nfe.wizard"
    _description = "Update Purchase Order lines from an imported NFe"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Financial Move",
        readonly=True,
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        related="move_id.partner_id",
        readonly=True,
    )

    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Purchase Order",
        readonly=True,
    )

    line_ids = fields.One2many(
        comodel_name="purchase.update.from.nfe.wizard.line",
        inverse_name="wizard_id",
        string="Order Lines",
    )

    @api.model
    def _get_wizard_vals_from_move(self, move):
        """Build the wizard values for a given vendor bill (imported NFe)."""
        move.ensure_one()
        purchase = self._find_purchase(move)
        line_vals = (
            self._prepare_wizard_line_vals_list(move, purchase) if purchase else []
        )
        return {
            "move_id": move.id,
            "purchase_id": purchase.id if purchase else False,
            "line_ids": [(0, 0, vals) for vals in line_vals],
        }

    @api.model
    def _find_purchase(self, move):
        """Find the unique draft/sent/purchase order that the NFe references.

        The buyer's purchase order reference (xPed) is stored on the invoice
        lines by l10n_br_account (partner_order, related to the imported fiscal
        document line), so we look the purchase up through those references.
        """
        refs = move.invoice_line_ids.filtered("partner_order").mapped("partner_order")
        if not refs:
            return False
        orders = (
            self.env["purchase.order.line"]
            .search(
                [
                    ("order_id.partner_id", "=", move.partner_id.id),
                    ("partner_order", "in", refs),
                ]
            )
            .order_id.filtered(lambda o: o.state in ("draft", "sent", "purchase"))
        )
        if len(orders) == 1:
            return orders
        return False

    @api.model
    def _prepare_wizard_line_vals_list(self, move, purchase):
        vals_list = []
        for nfe_line in move.invoice_line_ids.filtered("product_id"):
            po_line = self._match_po_line(nfe_line, purchase)
            if not po_line:
                continue
            vals_list.append(self._prepare_wizard_line_vals(nfe_line, po_line))
        return vals_list

    @api.model
    def _match_po_line(self, nfe_line, purchase):
        pol = self.env["purchase.order.line"]
        if nfe_line.partner_order:
            if nfe_line.partner_order_line:
                pol = pol.search(
                    [
                        ("order_id", "=", purchase.id),
                        ("partner_order", "=", nfe_line.partner_order),
                        ("partner_order_line", "=", nfe_line.partner_order_line),
                    ],
                    limit=1,
                )
            if not pol:
                pol = self.env["purchase.order.line"].search(
                    [
                        ("order_id", "=", purchase.id),
                        ("partner_order", "=", nfe_line.partner_order),
                        ("product_id", "=", nfe_line.product_id.id),
                    ],
                    limit=1,
                )
        if not pol:
            pol = self.env["purchase.order.line"].search(
                [
                    ("order_id", "=", purchase.id),
                    ("product_id", "=", nfe_line.product_id.id),
                    ("partner_order", "=", False),
                ],
                limit=1,
            )
        return pol

    @api.model
    def _prepare_wizard_line_vals(self, nfe_line, po_line):
        quantity = nfe_line.quantity
        price_unit = nfe_line.price_unit
        uom = nfe_line.uom_id or nfe_line.product_uom_id
        if uom and po_line.product_uom and uom != po_line.product_uom:
            factor = uom._compute_quantity(1.0, po_line.product_uom)
            quantity = nfe_line.quantity * factor
            price_unit = nfe_line.price_unit * factor
        return {
            "nfe_line_id": nfe_line.id,
            "po_line_id": po_line.id,
            "new_quantity": quantity,
            "new_price_unit": price_unit,
        }

    def action_apply(self):
        for line in self.line_ids:
            line._apply()
        return {"type": "ir.actions.act_window_close"}


class PurchaseUpdateFromNfeWizardLine(models.TransientModel):
    _name = "purchase.update.from.nfe.wizard.line"
    _description = "Purchase Order line updated from an imported NFe"

    wizard_id = fields.Many2one(
        comodel_name="purchase.update.from.nfe.wizard",
        ondelete="cascade",
    )

    nfe_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="NFe Line",
        readonly=True,
    )

    po_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Purchase Order Line",
        readonly=True,
    )

    partner_order = fields.Char(
        related="nfe_line_id.partner_order",
        string="PO Reference (xPed)",
        readonly=True,
    )

    partner_order_line = fields.Char(
        related="nfe_line_id.partner_order_line",
        string="PO Reference Line",
        readonly=True,
    )

    nfe_quantity = fields.Float(
        related="nfe_line_id.quantity",
        string="NFe Quantity",
        readonly=True,
    )

    nfe_price_unit = fields.Float(
        related="nfe_line_id.price_unit",
        string="NFe Unit Price",
        readonly=True,
    )

    po_quantity = fields.Float(
        related="po_line_id.product_qty",
        string="Current Quantity",
        readonly=True,
    )

    po_price_unit = fields.Float(
        related="po_line_id.price_unit",
        string="Current Unit Price",
        readonly=True,
    )

    new_quantity = fields.Float(string="Quantity")

    new_price_unit = fields.Float(string="Unit Price")

    update_taxes = fields.Boolean(
        default=True,
        help="Update the fiscal taxes of the purchase order line from the "
        "imported document.",
    )

    def _apply(self):
        self.ensure_one()
        line = self.po_line_id
        order = line.order_id
        if order.state not in ("draft", "sent", "purchase"):
            raise UserError(
                _(
                    "Cannot update the purchase order %(order)s in %(state)s state. "
                    "Only draft, sent or confirmed orders can be updated."
                )
                % {"order": order.name, "state": order.state}
            )
        vals = {
            "product_qty": self.new_quantity,
            "price_unit": self.new_price_unit,
        }
        if self.update_taxes:
            vals.update(self._prepare_fiscal_tax_vals())
        line.write(vals)
        if self.update_taxes:
            line._onchange_fiscal_tax_ids()
            line._compute_tax_fields()
        line._compute_amount()

    def _prepare_fiscal_tax_vals(self):
        """Copy the NFe fiscal fields that can be honored by the PO line."""
        nfe_line = self.nfe_line_id
        vals = {}
        for fname in _BILL_TO_PO_FISCAL_FIELDS:
            if (
                fname in nfe_line._fields
                and fname in self.po_line_id._fields
                and nfe_line[fname]
            ):
                vals[fname] = nfe_line[fname]
        return vals
