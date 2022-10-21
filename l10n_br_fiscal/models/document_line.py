# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DocumentLine(models.Model):
    _name = "l10n_br_fiscal.document.line"
    _inherit = "l10n_br_fiscal.document.line.mixin"
    _description = "Fiscal Document Line"

    @api.model
    def _operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    fiscal_operation_id = fields.Many2one(
        domain=lambda self: self._operation_domain(),
    )

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Document",
        ondelete="cascade",
    )

    # used mostly to enable _inherits of account.invoice on fiscal_document
    # when existing invoices have no fiscal document.
    active = fields.Boolean(
        default=True,
    )

    name = fields.Text()

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="document_id.company_id",
        store=True,
        string="Company",
    )

    tax_framework = fields.Selection(
        related="company_id.tax_framework",
    )

    partner_id = fields.Many2one(
        related="document_id.partner_id",
        store=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Currency",
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
    )

    ind_final = fields.Selection(related="document_id.ind_final")

    # Amount Fields
    amount_untaxed = fields.Monetary(
        compute="_compute_amounts",
    )

    amount_tax = fields.Monetary(
        compute="_compute_amounts",
    )

    amount_fiscal = fields.Monetary(
        compute="_compute_amounts",
    )

    amount_total = fields.Monetary(
        compute="_compute_amounts",
    )

    # Usado para tornar Somente Leitura os campos dos custos
    # de entrega quando a definição for por Total
    delivery_costs = fields.Selection(
        related="company_id.delivery_costs",
    )

    force_compute_delivery_costs_by_total = fields.Boolean(
        related="document_id.force_compute_delivery_costs_by_total"
    )

    def unlink(self):
        dummy_docs = self.env["res.company"].search([]).mapped("fiscal_dummy_id")
        if any(line.document_id in dummy_docs for line in self):
            raise UserError(_("You cannot unlink Fiscal Document Line Dummy !"))
        return super().unlink()
