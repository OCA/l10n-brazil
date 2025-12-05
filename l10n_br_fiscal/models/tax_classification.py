# Copyright (C) 2024  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.fiscal import TAX_DOMAIN_CBS, TAX_DOMAIN_IBS, TAX_DOMAIN_IS


class TaxClassification(models.Model):
    """
    Tax Classification for Brazilian Tax Reform (Reforma Tributária).

    This model represents the tax classification table used to determine
    how products and services will be taxed by the new taxes (IBS, CBS, IS)
    that will come into effect from 2026.
    """

    _name = "l10n_br_fiscal.tax.classification"
    _inherit = "l10n_br_fiscal.data.product.abstract"
    _description = "Tax Classification"
    _order = "code"

    code = fields.Char(size=10)

    code_unmasked = fields.Char(size=10)

    description = fields.Text()

    tax_ibs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="IBS Tax",
        domain=[("tax_domain", "=", TAX_DOMAIN_IBS)],
    )

    tax_cbs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="CBS Tax",
        domain=[("tax_domain", "=", TAX_DOMAIN_CBS)],
    )

    tax_is_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="IS Tax",
        domain=[("tax_domain", "=", TAX_DOMAIN_IS)],
    )

    effective_date = fields.Date()

    product_tmpl_ids = fields.One2many(inverse_name="tax_classification_id")

    tax_definition_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax.definition",
        relation="tax_classification_tax_definition_rel",  # (orm default is too long)
        readonly=True,
        string="Tax Definition",
    )
