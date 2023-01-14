# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# Copyright (C) 2021 - TODAY Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import PRODUCT_FISCAL_TYPE


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

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

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
    )

    fiscal_type = fields.Selection(selection=PRODUCT_FISCAL_TYPE, string="Tipo Fiscal")

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
        digits="Account",
    )

    insurance_value = fields.Float(
        digits="Account",
    )

    other_value = fields.Float(
        digits="Account",
    )

    total_with_taxes = fields.Float(
        digits="Account",
    )

    def _select(self):
        select_str = super()._select()
        select_str += """
            , l.fiscal_operation_id as fiscal_operation_id
            , l.fiscal_operation_line_id as fiscal_operation_line_id
            , l.cfop_id
            , l.fiscal_type
            , l.ncm_id
            , l.nbm_id
            , l.cest_id
            , SUM(l.icms_value) as icms_value
            , SUM(l.icmsst_value) as icmsst_value
            , SUM(l.ipi_value) as ipi_value
            , SUM(l.pis_value) as pis_value
            , SUM(l.cofins_value) as cofins_value
            , SUM(l.ii_value) as ii_value
            , SUM(l.freight_value) as freight_value
            , SUM(l.insurance_value) as insurance_value
            , SUM(l.other_value) as other_value
            , SUM(l.price_unit / COALESCE(NULLIF(po.currency_rate, 0), 1.0) * l.product_qty
            )::decimal(16,2)
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
            as total_with_taxes
        """
        return select_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += """
            , l.fiscal_operation_id
            , l.fiscal_operation_line_id
            , l.cfop_id
            , l.fiscal_type
            , l.ncm_id
            , l.nbm_id
            , l.cest_id
        """
        return group_by_str
