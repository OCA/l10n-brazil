# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    NFE_IND_PRES,
    NFE_IND_PRES_DEFAULT,
    PRODUCT_FISCAL_TYPE,
)


class SaleReport(models.Model):
    _inherit = "sale.report"

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        readonly=True,
    )

    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Fiscal Operation Line",
        readonly=True,
    )

    ind_pres = fields.Selection(
        selection=NFE_IND_PRES,
        string="Buyer Presence",
        default=NFE_IND_PRES_DEFAULT,
    )

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
    )

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE, string="Product Fiscal Type"
    )

    cest_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cest",
        string="CEST",
    )

    ncm_id = fields.Many2one(comodel_name="l10n_br_fiscal.ncm", string="NCM")

    nbm_id = fields.Many2one(comodel_name="l10n_br_fiscal.nbm", string="NBM")

    icms_value = fields.Float(
        string="ICMS Value",
        digits="Account",
    )

    icmsst_value = fields.Float(
        string="ICMS ST Value",
        digits="Account",
    )

    ipi_value = fields.Float(
        string="IPI Value",
        digits="Account",
    )

    pis_value = fields.Float(
        string="PIS Value",
        digits="Account",
    )

    cofins_value = fields.Float(
        string="COFINS Value",
        digits="Account",
    )

    ii_value = fields.Float(
        string="II Value",
        digits="Account",
    )

    freight_value = fields.Float(
        string="Freight Value",
        digits="Account",
    )

    insurance_value = fields.Float(
        string="Insurance Value",
        digits="Account",
    )

    other_value = fields.Float(
        string="Other Value",
        digits="Account",
    )

    total_with_taxes = fields.Float(
        string="Total with Taxes",
        digits="Account",
    )

    def _query(self, with_clause="", fields=None, groupby="", from_clause=""):
        if fields is None:
            fields = {}

        fields.update(
            {
                "fiscal_operation_id": ", l.fiscal_operation_id as fiscal_operation_id",
                "fiscal_operation_line_id": (
                    ", l.fiscal_operation_line_id as fiscal_operation_line_id"
                ),
                "ind_pres": ", s.ind_pres",
                "cfop_id": ", l.cfop_id as cfop_id",
                "fiscal_type": ", l.fiscal_type as fiscal_type",
                "ncm_id": ", l.ncm_id as ncm_id",
                "nbm_id": ", l.nbm_id as nbm_id",
                "cest_id": ", l.cest_id as cest_id",
                "icms_value": ", SUM(l.icms_value) as icms_value",
                "icmsst_value": ", SUM(l.icmsst_value) as icmsst_value",
                "ipi_value": ", SUM(l.ipi_value) as ipi_value",
                "cofins_value": ", SUM(l.cofins_value) as cofins_value",
                "pis_value": ", SUM(l.pis_value) as pis_value",
                "ii_value": ", SUM(l.ii_value) as ii_value",
                "freight_value": ", SUM(l.freight_value) as freight_value",
                "insurance_value": ", SUM(l.insurance_value) as insurance_value",
                "other_value": ", SUM(l.other_value) as other_value",
                "total_with_taxes": """
                    , SUM(l.price_total / CASE COALESCE(s.currency_rate, 0)
                        WHEN 0 THEN 1.0 ELSE s.currency_rate END)
                    + SUM(CASE WHEN l.ipi_value IS NULL THEN
                       0.00 ELSE l.ipi_value END)
                    + SUM(CASE WHEN l.icmsst_value IS NULL THEN
                       0.00 ELSE l.icmsst_value END)
                    + SUM(CASE WHEN l.freight_value IS NULL THEN
                       0.00 ELSE l.freight_value END)
                    + SUM(CASE WHEN l.insurance_value IS NULL THEN
                       0.00 ELSE l.insurance_value END)
                    + SUM(CASE WHEN l.other_value IS NULL THEN
                       0.00 ELSE l.other_value END)
                    as total_with_taxes""",
            }
        )
        groupby += """
            , l.fiscal_operation_id
            , l.fiscal_operation_line_id
            , s.ind_pres
            , l.cfop_id
            , l.fiscal_type
            , l.ncm_id
            , l.nbm_id
            , l.cest_id
        """
        return super()._query(
            with_clause=with_clause,
            fields=fields,
            groupby=groupby,
            from_clause=from_clause,
        )
