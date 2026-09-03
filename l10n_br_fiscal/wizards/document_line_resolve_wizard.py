# Copyright (C) 2026  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# The internal price of a resolved line is warned when it deviates from the
# last learned supplier price by more than this fraction. The de-para keeps
# the line total invariant, so a wrong conversion factor never shows up in the
# total: the only place it surfaces is the resulting unit price against
# history. This is the net that the total cannot be.
PRICE_WARNING_RATIO = 0.20


class DocumentLineResolveWizard(models.TransientModel):
    _name = "l10n_br_fiscal.document.line.resolve.wizard"
    _description = "Resolve an imported document line (mapping in one place)"

    line_id = fields.Many2one(
        "l10n_br_fiscal.document.line", required=True, ondelete="cascade"
    )
    mode = fields.Selection(
        [("link", "Link to an existing product"), ("create", "Create a new product")],
        required=True,
        default="link",
    )

    # what the supplier declared, read only, from the file
    partner_name = fields.Char(readonly=True)
    partner_product_code = fields.Char(readonly=True)
    partner_uom_code = fields.Char(readonly=True)
    partner_quantity = fields.Float(readonly=True)
    partner_price_unit = fields.Float(readonly=True)
    partner_ncm_code = fields.Char(readonly=True)
    partner_cfop_id = fields.Many2one("l10n_br_fiscal.cfop", readonly=True)
    cfop_warning = fields.Char(readonly=True)

    # the internal de-para the reviewer confirms
    product_id = fields.Many2one("product.product")
    import_uom_id = fields.Many2one("uom.uom", string="Internal UoM")
    import_uom_factor = fields.Float(string="Conversion Factor", default=1.0)
    fiscal_operation_id = fields.Many2one(
        "l10n_br_fiscal.operation", string="Inbound Fiscal Operation"
    )
    fiscal_operation_suggested = fields.Boolean(readonly=True)

    # live preview, computed, never written to the line
    internal_quantity = fields.Float(compute="_compute_preview", readonly=True)
    internal_price_unit = fields.Float(compute="_compute_preview", readonly=True)
    total_check = fields.Monetary(
        compute="_compute_preview", readonly=True, currency_field="currency_id"
    )
    currency_id = fields.Many2one("res.currency", readonly=True)
    price_warning = fields.Char(compute="_compute_preview", readonly=True)

    @api.depends(
        "import_uom_factor", "partner_quantity", "partner_price_unit", "product_id"
    )
    def _compute_preview(self):
        for wizard in self:
            factor = wizard.import_uom_factor or 1.0
            wizard.internal_quantity = wizard.partner_quantity * factor
            wizard.internal_price_unit = (
                wizard.partner_price_unit / factor if factor else 0.0
            )
            wizard.total_check = wizard.partner_quantity * wizard.partner_price_unit
            wizard.price_warning = wizard._price_warning()

    def _price_warning(self):
        """Compare the resulting internal unit price against the last price
        learned for this supplier and code. The total is invariant to the
        factor by construction, so this is the only signal a wrong conversion
        leaves."""
        self.ensure_one()
        if not (self.product_id and self.partner_product_code):
            return ""
        partner = self.line_id.document_id.partner_id
        seller = self.env["product.supplierinfo"].search(
            [
                ("partner_id", "=", partner.id),
                ("product_code", "=", self.partner_product_code),
                ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
            ],
            limit=1,
        )
        if not seller or not seller.price:
            return ""
        internal = self.internal_price_unit
        if not internal:
            return ""
        ratio = abs(internal - seller.price) / seller.price
        if ratio > PRICE_WARNING_RATIO:
            return _(
                "Warning: the resulting unit price (%(now).2f) is %(pct).0f%% "
                "away from the last purchase from this supplier (%(last).2f). "
                "Check the conversion factor before resolving."
            ) % {
                "now": internal,
                "pct": ratio * 100,
                "last": seller.price,
            }
        return ""

    @api.onchange("mode")
    def _onchange_mode(self):
        if self.mode == "create":
            self.product_id = False

    def _apply(self):
        self.ensure_one()
        line = self.line_id
        if self.mode == "create":
            if not self.import_uom_id:
                raise UserError(
                    _("Choose the internal unit before creating the product.")
                )
            line.import_uom_id = self.import_uom_id
            line.import_uom_factor = self.import_uom_factor or 1.0
            if self.fiscal_operation_id:
                line.fiscal_operation_id = self.fiscal_operation_id
            line.action_create_product_from_line()
        else:
            if not self.product_id:
                raise UserError(_("Choose the internal product to link."))
            line._apply_import_depara(
                product=self.product_id,
                uom=self.import_uom_id,
                factor=self.import_uom_factor,
                fiscal_operation=self.fiscal_operation_id,
            )

    def action_resolve(self):
        self._apply()
        return {"type": "ir.actions.act_window_close"}

    def action_resolve_next(self):
        line = self.line_id
        self._apply()
        return line._open_next_pending_resolve_wizard()
