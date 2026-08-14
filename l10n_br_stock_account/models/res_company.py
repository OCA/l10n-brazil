# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    stock_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        domain=[("state", "=", "approved")],
    )

    stock_in_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        domain=[("state", "=", "approved"), ("fiscal_operation_type", "=", "in")],
    )

    stock_out_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        domain=[("state", "=", "approved"), ("fiscal_operation_type", "=", "out")],
    )

    stock_valuation_via_stock_price = fields.Boolean(
        string="Valuation Via Stock Price",
        default=False,
        help="Whether stock is valued at the Odoo default price or at the net"
        " acquisition cost, that is, the invoice total minus the taxes this"
        " company can recover (art. 301 RIR/2018, CPC 16).\n\n"
        "    * True values incoming stock net of recoverable taxes.\n"
        "    Opt-in: the False default keeps existing databases unchanged.",
    )

    def _net_cost_unsupported_categories(self):
        """Product categories the net cost valuation cannot reach.

        The flag is enabled per company, but whether the net cost actually
        reaches the ledger is decided per product category:

        * standard costing prices the valuation layer from the product
          standard price, so the move price is computed and dropped;
        * periodic inventory books no entry on receipt at all, so a net cost
          on the layer would face a gross cost on the ledger, leaving two
          defensible numbers for the same stock.

        Used to warn on the settings screen. Enabling the flag is not
        blocked, because both settings above are the Odoo defaults and a
        company may well hold categories it no longer moves; what protects
        the ledger is stock.move refusing to apply the net cost there.
        """
        self.ensure_one()
        categories = (
            self.env["product.product"]
            .with_company(self)
            .search([("type", "=", "product")])
            .categ_id
        )
        return categories.filtered(
            lambda categ: categ.property_cost_method == "standard"
            or categ.property_valuation == "manual_periodic"
        )
