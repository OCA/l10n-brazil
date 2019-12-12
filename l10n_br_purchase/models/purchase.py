# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "l10n_br_fiscal.document.mixin"]

    @api.one
    @api.depends(
        "order_line.price_unit", "order_line.product_qty", "order_line.taxes_id"
    )
    def _compute_amount(self):
        amount_untaxed = 0.0
        amount_tax = 0.0

        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                if order.company_id.tax_calculation_rounding_method == "round_globally":
                    taxes = line.taxes_id.compute_all(
                        line.price_unit,
                        line.order_id.currency_id,
                        line.product_qty,
                        product=line.product_id,
                        partner=line.order_id.partner_id,
                    )
                    amount_tax += sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    )
                else:
                    amount_tax += line.price_tax
            order.update(
                {
                    "amount_untaxed": order.currency_id.round(amount_untaxed),
                    "amount_tax": order.currency_id.round(amount_tax),
                    "amount_total": amount_untaxed + amount_tax,
                }
            )

        self.amount_untaxed = self.currency_id.round(amount_untaxed)
        self.amount_tax = self.currency_id.round(amount_tax)
        self.amount_total = self.currency_id.round(amount_untaxed + amount_tax)

    @api.model
    @api.returns("l10n_br_account.fiscal_category")
    def _default_fiscal_category(self):
        company = self.env["res.company"].browse(self.env.user.company_id.id)
        return company.purchase_fiscal_category_id

    amount_untaxed = fields.Monetary(
        compute="_compute_amount",
        digits=dp.get_precision("Purchase Price"),
        string="Untaxed Amount",
        store=True,
        help="The amount without tax",
    )
    amount_tax = fields.Monetary(
        compute="_compute_amount",
        digits=dp.get_precision("Purchase Price"),
        string="Taxes",
        store=True,
        help="The tax amount",
    )
    amount_total = fields.Monetary(
        compute="_compute_amount",
        digits=dp.get_precision("Purchase Price"),
        string="Total",
        store=True,
        help="The total amount",
    )

    cnpj_cpf = fields.Char(string="CNPJ/CPF", related="partner_id.cnpj_cpf")

    legal_name = fields.Char(string="Razão Social", related="partner_id.legal_name")

    ie = fields.Char(string="Inscrição Estadual", related="partner_id.inscr_est")
