# Copyright 2021 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class FiscalLineMixin(models.AbstractModel):
    _name = "l10n_br_repair.fiscal.line.mixin"
    _inherit = ["l10n_br_fiscal.document.line.mixin"]
    _description = "Repair Fiscal Line Mixin"

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.repair_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        return [("state", "=", "approved")]

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    # adapted for _compute_ind_final and the fiscal partner
    def _get_document(self):
        self.ensure_one()
        return self.repair_id

    def _get_fiscal_partner(self):
        self.ensure_one()
        return self.repair_id.partner_invoice_id or self.repair_id.partner_id

    def _compute_l10n_br_repair_tax_id(self):
        """Account taxes follow the fiscal taxes when there is a fiscal
        operation line, otherwise the value set by the core is kept."""
        for line in self:
            if line.fiscal_operation_line_id and line.product_id:
                line.tax_id = line.fiscal_tax_ids.account_taxes(
                    user_type="sale",
                    fiscal_operation=line.fiscal_operation_id,
                    company=line.company_id,
                )
            else:
                line.tax_id = line.tax_id

    def _compute_l10n_br_repair_amounts(self):
        for line in self.filtered("fiscal_operation_id"):
            line.price_subtotal = line.fiscal_amount_untaxed
            line.price_total = line.fiscal_amount_total

    def _prepare_br_invoice_line(self, fiscal_position, name):
        self.ensure_one()
        product = self.product_id.with_company(self.company_id)
        account = product.product_tmpl_id.get_product_accounts(
            fiscal_pos=fiscal_position
        )["income"]
        if not account:
            raise UserError(
                _(
                    'No account defined for product "%(product)s".',
                    product=product.display_name,
                )
            )
        vals = self._prepare_br_fiscal_dict()
        vals.update(
            {
                "name": name,
                "account_id": account.id,
                "quantity": self.product_uom_qty,
                "tax_ids": [Command.set(self.tax_id.ids)],
                "product_uom_id": self.product_uom.id,
                "price_unit": self.price_unit,
                "product_id": self.product_id.id,
            }
        )
        return vals
