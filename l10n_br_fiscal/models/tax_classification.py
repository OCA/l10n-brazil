# Copyright (C) 2024  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class TaxClassification(models.Model):
    """
    Tax Classification for Brazilian Tax Reform (Reforma Tributária).

    This model represents the tax classification table (cClassTrib) from
    the Brazilian Tax Reform (LC 214/2025). It stores the three main fields:
    - code (cClassTrib): The classification code
    - name (Nome cClassTrib): The classification name
    - description (Descrição cClassTrib): The detailed description

    The tax treatment (IBS, CBS, IS) is defined separately in Tax Definition,
    not directly in the classification itself.
    """

    _name = "l10n_br_fiscal.tax.classification"
    _inherit = "l10n_br_fiscal.data.product.abstract"
    _description = "Tax Classification"
    _order = "code"

    code = fields.Char(size=10)

    code_unmasked = fields.Char(size=10)

    description = fields.Text(
        help="Descrição cClassTrib - Detailed description of the tax classification",
    )

    product_tmpl_ids = fields.One2many(
        comodel_name="product.template",
        inverse_name="tax_classification_id",
        string="Products",
        readonly=True,
    )

    tax_definition_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax.definition",
        relation="tax_classification_tax_definition_rel",  # (orm default is too long)
        readonly=True,
        string="Tax Definitions",
        help="Tax definitions that reference this classification",
    )
