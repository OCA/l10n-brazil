# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nBrPosProductFiscalMap(models.Model):
    _name = "l10n_br_pos.product_fiscal_map"
    _description = "Pos Product Fiscal Map"
    _inherit = "l10n_br_fiscal.document.line.mixin"

    name = fields.Char()

    partner_id = fields.Many2one(
        comodel_name="res.partner",
    )

    quantity = fields.Float(
        default=1,
        readonly=True,
    )

    price_unit = fields.Float(
        default=1,
        readonly=True,
    )

    pos_config_id = fields.Many2one(
        comodel_name="pos.config",
    )

    fiscal_operation_id = fields.Many2one(
        related="pos_config_id.out_pos_fiscal_operation_id"
    )

    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
    )

    product_id = fields.Many2one(
        related="product_tmpl_id.product_variant_id",
    )

    company_id = fields.Many2one(
        related="pos_config_id.company_id",
    )
    tax_framework = fields.Selection(
        related="company_id.tax_framework",
        string="Tax Framework",
    )

    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="pos_fiscal_map_tax_rel",
        column1="pos_fiscal_map_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="pos_fiscal_map_comment_rel",
        column1="pos_fiscal_map_id",
        column2="comment_id",
        string="Comments",
    )

    ncm_code = fields.Char(
        related="ncm_id.code_unmasked",
    )

    cfop_code = fields.Char(
        related="cfop_id.code",
    )

    ncm_code_exception = fields.Char(
        related="ncm_id.exception",
    )

    company_tax_framework = fields.Selection(
        related="company_id.tax_framework",
    )

    ind_final = fields.Selection(related="partner_id.ind_final")

    def _get_product_price(self):
        self.price_unit = 1
