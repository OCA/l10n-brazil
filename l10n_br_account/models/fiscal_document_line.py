# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    # the following fields collide with account.invoice.line fields so we use
    # related field alias to be able to write them through account.invoice.line
    fiscal_doc_line_name = fields.Text(
        related="name",
        string="Fiscal Doc Name",
        readonly=False)

    fiscal_doc_line_partner_id = fields.Many2one(
        related="partner_id",
        string="Fiscal Doc Partner",
        readonly=False)

    fiscal_doc_line_company_id = fields.Many2one(
        related="company_id",
        string="Fiscal Doc Company",
        readonly=False)

    fiscal_doc_line_currency_id = fields.Many2one(
        related="currency_id",
        string="Fiscal Doc Currency",
        readonly=False)

    fiscal_doc_line_product_id = fields.Many2one(
        related="product_id",
        string="Fiscal Doc Product",
        readonly=False)

    fiscal_doc_line_uom_id = fields.Many2one(
        related="uom_id",
        string="Fiscal Doc UOM",
        readonly=False)

    fiscal_doc_line_quantity = fields.Float(
        related="quantity",
        string="Fiscal Doc Quantity",
        readonly=False)

    fiscal_doc_line_price_unit = fields.Float(
        related="price_unit",
        string="Fiscal Doc Price Unit",
        readonly=False)

    fiscal_doc_line_discount = fields.Monetary(
        related="discount_value",
        string="Fiscal Doc  Discount Value",
        readonly=False)
