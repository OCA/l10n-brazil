# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import TAX_FRAMEWORK


class DocumentLineAbstract(models.AbstractModel):
    _name = "l10n_br_fiscal.document.line.abstract"
    _inherit = "l10n_br_fiscal.document.line.mixin"
    _description = "Fiscal Document Line Abstract"

    @api.depends(
        "fiscal_price",
        "discount_value",
        "insurance_value",
        "other_costs_value",
        "freight_value",
        "fiscal_quantity",
        "amount_tax_not_included",
        "uot_id",
        "product_id",
        "document_id.partner_id",
        "document_id.company_id")
    def _compute_amount(self):
        for record in self:
            round_curr = record.document_id.currency_id.round
            record.amount_untaxed = round_curr(
                record.price_unit * record.quantity)
            record.amount_tax = record.amount_tax_not_included
            record.amount_total = (
                record.amount_untaxed +
                record.amount_tax +
                record.insurance_value +
                record.other_costs_value +
                record.freight_value -
                record.discount_value)

    # used mostly to enable _inherits of account.invoice on fiscal_document
    # when existing invoices have no fiscal document.
    active = fields.Boolean(
        string="Active",
        default=True)

    name = fields.Text(string="Name")

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.abstract",
        string="Document")

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="document_id.company_id",
        store=True,
        string="Company")

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="company_id.tax_framework",
        string="Tax Framework")

    partner_id = fields.Many2one(
        related="document_id.partner_id")

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Currency")

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product")

    notes = fields.Text(
        string="Notes")

    # Amount Fields
    amount_estimate_tax = fields.Monetary(
        string="Amount Estimate Total",
        compute="_compute_amount",
        default=0.00)

    amount_untaxed = fields.Monetary(
        string="Amount Untaxed",
        compute="_compute_amount",
        default=0.00)

    amount_tax = fields.Monetary(
        string="Amount Tax",
        compute="_compute_amount",
        default=0.00)

    amount_total = fields.Monetary(
        string="Amount Total",
        compute="_compute_amount",
        default=0.00)
