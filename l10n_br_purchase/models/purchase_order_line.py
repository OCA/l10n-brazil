# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.purchase_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        domain = [
            ("state", "=", "approved"),
            ("fiscal_type", "in", ("purchase", "other", "purchase_refund")),
        ]
        return domain

    # Adapt Mixin's fields
    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    # This redundancy is necessary for the system to be able to load the report
    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
        domain="[('fiscal_operation_id', '=', fiscal_operation_id), "
        "('state', '=', 'approved')]",
    )

    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_purchase_line_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    quantity = fields.Float(
        string="Mixin Quantity",
        related="product_qty",
        depends=["product_qty"],
    )

    uom_id = fields.Many2one(
        string="Mixin UOM",
        related="product_uom",
        depends=["product_uom"],
    )

    tax_framework = fields.Selection(
        related="order_id.company_id.tax_framework",
        string="Tax Framework",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="purchase_order_line_comment_rel",
        column1="purchase_line_id",
        column2="comment_id",
        string="Comments",
    )

    ind_final = fields.Selection(related="order_id.ind_final")

    # Usado para tornar Somente Leitura os campos totais dos custos
    # de entrega quando a definição for por Linha
    delivery_costs = fields.Selection(
        related="company_id.delivery_costs",
    )

    @api.depends(
        "product_uom_qty",
        "price_unit",
        "fiscal_price",
        "fiscal_quantity",
        "discount_value",
        "freight_value",
        "insurance_value",
        "other_value",
        "taxes_id",
    )
    def _compute_amount(self):
        """Compute the amounts of the PO line."""
        result = super()._compute_amount()
        for line in self:
            if line.fiscal_operation_id:
                # Update taxes fields
                line._update_fiscal_taxes()
                # Call mixin compute method
                line._compute_amounts()
                # Update record
                line.update(
                    {
                        "price_subtotal": line.amount_untaxed,
                        "price_tax": line.amount_tax,
                        "price_gross": line.amount_untaxed + line.discount_value,
                        "price_total": line.amount_total,
                    }
                )
        return result

    @api.onchange("product_qty", "product_uom")
    def _onchange_quantity(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        return self._onchange_commercial_quantity()

    def _compute_tax_id(self):
        for line in self:
            if line.fiscal_operation_line_id:
                res = super()._compute_tax_id()
                line.taxes_id = line.fiscal_tax_ids.account_taxes(
                    user_type="purchase", fiscal_operation=line.fiscal_operation_id
                )
            else:
                res = None
            return res

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        if self.fiscal_operation_line_id:
            res = super()._onchange_fiscal_tax_ids()
            self.taxes_id = self.fiscal_tax_ids.account_taxes(
                user_type="purchase", fiscal_operation=self.fiscal_operation_id
            )
        else:
            res = None
        return res

    def _prepare_account_move_line(self, move=False):
        values = super()._prepare_account_move_line(move)
        if values.get("purchase_line_id"):
            line = self.env["purchase.order.line"].browse(
                values.get("purchase_line_id")
            )
            if line.fiscal_operation_id:
                # O caso Brasil se caracteriza por ter a Operação Fiscal
                fiscal_values = line._prepare_br_fiscal_dict()
                fiscal_values.update(values)
                values.update(fiscal_values)

        return values
