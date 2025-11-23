# Copyright (C) 2016-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

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

    service_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type",
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
    )

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
    )

    fiscal_type = fields.Selection(selection=PRODUCT_FISCAL_TYPE)

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
    )

    icms_value = fields.Float(string="Valor ICMS", digits="Account")

    icmsst_value = fields.Float(string="Valor ICMS ST", digits="Account")

    icms_origin_value = fields.Float(string="Valor Difal Origem", digits="Account")

    icms_destination_value = fields.Float(
        string="Valor Difal Destino",
        digits="Account",
    )

    icmsfcp_value = fields.Float(string="Valor Difal FCP", digits="Account")

    ipi_value = fields.Float(string="IPI Value", digits="Account")

    pis_value = fields.Float(string="PIS Value", digits="Account")

    cofins_value = fields.Float(string="COFINS Value", digits="Account")

    ii_value = fields.Float(string="II Value", digits="Account")

    issqn_value = fields.Float(digits="Account")

    freight_value = fields.Float(digits="Account")

    insurance_value = fields.Float(digits="Account")

    other_value = fields.Float(digits="Account")

    discount_value = fields.Float(digits="Account")

    cest_id = fields.Many2one(comodel_name="l10n_br_fiscal.cest", string="CEST")

    ncm_id = fields.Many2one(comodel_name="l10n_br_fiscal.ncm", string="NCM")

    nbm_id = fields.Many2one(comodel_name="l10n_br_fiscal.nbm", string="NBM")

    @api.model
    def _select(self):
        select_str = super()._select()
        select_str += """
            , fd.issuer
            , fd.document_type_id
            , fd.document_serie_id
            , fdl.fiscal_operation_id
            , fdl.fiscal_operation_line_id
            , fdl.service_type_id
            , fdl.cfop_id
            , fdl.ncm_id
            , fdl.nbm_id
            , fdl.cest_id
            , fdl.fiscal_type
            , fdl.icms_value
            , fdl.icms_origin_value
            , fdl.icms_destination_value
            , fdl.icmsfcp_value
            , fdl.icmsst_value
            , fdl.ipi_value
            , fdl.pis_value
            , fdl.cofins_value
            , fdl.ii_value
            , fdl.issqn_value
            , fdl.freight_value
            , fdl.insurance_value
            , fdl.other_value
            , fdl.discount_value
        """
        return select_str

    @api.model
    def _from(self):
        from_str = super()._from()
        from_str += """
            LEFT JOIN l10n_br_fiscal_document fd ON
             fd.id = move.fiscal_document_id
            LEFT JOIN l10n_br_fiscal_document_line fdl ON
             fdl.id = line.fiscal_document_line_id
        """
        return from_str
