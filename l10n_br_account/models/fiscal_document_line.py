# Copyright (C) 2021 - TODAY Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    account_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="fiscal_document_line_id",
        string="Invoice Lines",
    )

    # proxy fields to enable writing the related (shadowed) fields
    # to the fiscal doc line from the aml through the _inherits system
    # despite they have the same names.
    fiscal_name = fields.Text(
        string="Fiscal Name",
        related="name",
        readonly=False,
    )
    fiscal_product_id = fields.Many2one(
        string="Fiscal Product",
        related="product_id",
        readonly=False,
    )
    fiscal_quantity = fields.Float(
        string="Fiscal Quantity",
        related="quantity",
        readonly=False,
    )
    fiscal_price_unit = fields.Float(
        string="Fiscal Price Unit",
        related="price_unit",
        readonly=False,
    )
    amount_tax_included_from_tax_values = fields.Float(
        compute="_compute_amount_tax_from_tax_values",
        help="Used on imported or edited fiscal documents",
    )
    amount_tax_excluded_from_tax_values = fields.Float(
        compute="_compute_amount_tax_excluded_from_tax_values",
        help="Used on imported or edited fiscal documents",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        It's not allowed to create a fiscal document line without a document_id anyway.
        But instead of letting Odoo crash in this case we simply avoid creating the
        record. This makes it possible to create an account.move.line without
        a fiscal_document_line_id: Odoo will write NULL as the value in this case.
        This is a requirement to allow account moves without fiscal documents despite
        the _inherits system.
        """

        if self._context.get("create_from_move_line"):
            if not any(vals.get("document_id") for vals in vals_list):
                return []

        return super().create(vals_list)

    def _compute_amount_tax_from_tax_values(self, included=True):
        included_taxes = (
            self.env["l10n_br_fiscal.tax.group"]
            .search([("tax_include", "=", included)])
            .mapped("tax_domain")
        )
        for line in self:
            for tax in included_taxes:
                if not hasattr(line, "%s_value" % (tax,)):
                    continue
                if included:
                    line.amount_tax_included_from_tax_values += getattr(
                        line, "%s_value" % (tax,)
                    )
                else:
                    line.amount_tax_excluded_from_tax_values += getattr(
                        line, "%s_value" % (tax,)
                    )

    def _compute_amount_tax_excluded_from_tax_values(self):
        self._compute_amount_tax_from_tax_values(included=False)
