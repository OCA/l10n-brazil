# Copyright 2021 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FiscalLineMixin(models.AbstractModel):
    _name = "l10n_br_repair.fiscal.line.mixin"
    _inherit = ["l10n_br_fiscal.document.line.mixin"]
    _description = "Fiscal Line Mixin"

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.repair_fiscal_operation_id

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    price_gross = fields.Monetary(
        compute="_compute_price_subtotal",
        string="Gross Amount",
        default=0.00,
    )

    price_total = fields.Monetary(
        compute="_compute_price_subtotal",
        default=0.00,
    )

    price_subtotal = fields.Float(
        "Subtotal",
        compute="_compute_price_subtotal",
        digits="Product Price",
    )

    fiscal_operation_type = fields.Selection(string="Fiscal Operation Type")

    @api.model
    def _fiscal_operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    def _prepare_invoice_line(self):
        self.ensure_one()
        product = self.product_id.with_company(self.company_id.id)
        partner_invoice = self.repair_id.partner_invoice_id or self.repair_id.partner_id
        fpos = self.env["account.fiscal.position"].get_fiscal_position(
            partner_invoice.id, delivery_id=self.repair_id.address_id.id
        )
        account = product.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)[
            "income"
        ]
        res = {
            "name": self.name,
            "account_id": account.id,
            "quantity": self.product_uom_qty,
            "tax_ids": [(6, 0, self.tax_id.ids)],
            "product_uom_id": self.product_uom.id,
            "price_unit": self.price_unit,
            "product_id": self.product_id.id,
        }
        res.update(self._prepare_br_fiscal_dict())
        return res

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        if self.product_id and self.fiscal_operation_line_id:
            super()._onchange_fiscal_tax_ids()
            self.tax_id = self.fiscal_tax_ids.account_taxes(
                user_type="sale", fiscal_operation=self.fiscal_operation_id
            )

    @api.onchange("product_uom", "product_uom_qty")
    def _onchange_product_uom(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        self._onchange_commercial_quantity()
