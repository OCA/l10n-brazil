# Copyright (C) 2016-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER,
    PRODUCT_FISCAL_TYPE,
)


class AccountInvoiceReport(models.Model):

    _inherit = "account.invoice.report"

    issuer = fields.Selection(
        selection=DOCUMENT_ISSUER,
    )

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operation",
    )

    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
    )

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
    )

    fiscal_type = fields.Selection(selection=PRODUCT_FISCAL_TYPE, string="Tipo Fiscal")

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
    )

    icms_value = fields.Float(string="Valor ICMS", digits="Account")

    icmsst_value = fields.Float(string="Valor ICMS ST", digits="Account")

    ipi_value = fields.Float(string="Valor IPI", digits="Account")

    pis_value = fields.Float(string="Valor PIS", digits="Account")

    cofins_value = fields.Float(string="Valor COFINS", digits="Account")

    ii_value = fields.Float(string="Valor II", digits="Account")

    total_with_taxes = fields.Float(string="Total com Impostos", digits="Account")
    cest_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cest",
        string="CEST",
    )

    ncm_id = fields.Many2one(comodel_name="l10n_br_fiscal.ncm", string="NCM")

    def _select(self):
        select_str = super()._select()
        select_str += """
            , sub.issuer
            , sub.document_type_id
            , sub.document_serie_id
            , sub.fiscal_operation_id
            , sub.fiscal_operation_line_id
            , sub.cfop_id
            , sub.ncm_id
            , sub.cest_id
            , sub.fiscal_type
            , sub.icms_value
            , sub.icmsst_value
            , sub.ipi_value
            , sub.pis_value
            , sub.cofins_value
            , sub.ii_value
            , sub.total_with_taxes
        """
        return select_str

    def _sub_select(self):
        select_str = super()._sub_select()

        select_str += """
            , fd.issuer
            , fd.document_type_id
            , fd.document_serie_id
            , fdl.fiscal_operation_id
            , fdl.fiscal_operation_line_id
            , fdl.cfop_id
            , fdl.ncm_id
            , fdl.cest_id
            , fdl.fiscal_type
            , SUM(fdl.icms_value) as icms_value
            , SUM(fdl.icmsst_value) as icmsst_value
            , SUM(fdl.ipi_value) as ipi_value
            , SUM(fdl.pis_value) as pis_value
            , SUM(fdl.cofins_value) as cofins_value
            , SUM(fdl.ii_value) as ii_value
            , SUM(
            ail.price_subtotal + fdl.ipi_value +
            fdl.icmsst_value + fdl.freight_value +
            fdl.insurance_value + fdl.other_value)
            as total_with_taxes
        """
        return select_str

    def _from(self):
        from_str = super()._from()
        from_str += """
            LEFT JOIN l10n_br_fiscal_document fd ON
             fd.id = ai.fiscal_document_id
            LEFT JOIN l10n_br_fiscal_document_line fdl ON
             fdl.id = ail.fiscal_document_line_id
            LEFT JOIN product_product prd ON prd.id = ail.product_id
            LEFT JOIN product_template prd_tmpl ON
             prd_tmpl.id = prd.product_tmpl_id
        """
        return from_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += """
                , fd.issuer
                , fd.document_type_id
                , fd.document_serie_id
                , fdl.fiscal_operation_id
                , fdl.fiscal_operation_line_id
                , fdl.cfop_id
                , fdl.ncm_id
                , fdl.cest_id
                , fdl.fiscal_type
        """
        return group_by_str
