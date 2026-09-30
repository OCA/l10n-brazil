# Copyright (C) 2016-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import SQL

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
        string="Fiscal Document Type",
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

    def _select_list(self, table):
        """Add the Brazilian fiscal columns to the invoice statistics.

        Odoo 20.0 builds the report with the TableSQL API: the fiscal
        document (line) is joined explicitly through its delegated fields
        instead of the removed _select()/_from() string hooks of 19.0.
        """
        fiscal_document = table._join("fiscal_document_id")
        fiscal_document_line = table._join("fiscal_document_line_id")
        return super()._select_list(table) + [
            SQL("%s AS issuer", fiscal_document.issuer),
            SQL("%s AS document_type_id", fiscal_document.document_type_id),
            SQL("%s AS document_serie_id", fiscal_document.document_serie_id),
            SQL(
                "%s AS fiscal_operation_id",
                fiscal_document_line.fiscal_operation_id,
            ),
            SQL(
                "%s AS fiscal_operation_line_id",
                fiscal_document_line.fiscal_operation_line_id,
            ),
            SQL("%s AS service_type_id", fiscal_document_line.service_type_id),
            SQL("%s AS cfop_id", fiscal_document_line.cfop_id),
            SQL("%s AS ncm_id", fiscal_document_line.ncm_id),
            SQL("%s AS nbm_id", fiscal_document_line.nbm_id),
            SQL("%s AS cest_id", fiscal_document_line.cest_id),
            SQL("%s AS fiscal_type", fiscal_document_line.fiscal_type),
            SQL("%s AS icms_value", fiscal_document_line.icms_value),
            SQL(
                "%s AS icms_origin_value",
                fiscal_document_line.icms_origin_value,
            ),
            SQL(
                "%s AS icms_destination_value",
                fiscal_document_line.icms_destination_value,
            ),
            SQL("%s AS icmsfcp_value", fiscal_document_line.icmsfcp_value),
            SQL("%s AS icmsst_value", fiscal_document_line.icmsst_value),
            SQL("%s AS ipi_value", fiscal_document_line.ipi_value),
            SQL("%s AS pis_value", fiscal_document_line.pis_value),
            SQL("%s AS cofins_value", fiscal_document_line.cofins_value),
            SQL("%s AS ii_value", fiscal_document_line.ii_value),
            SQL("%s AS issqn_value", fiscal_document_line.issqn_value),
            SQL("%s AS freight_value", fiscal_document_line.freight_value),
            SQL("%s AS insurance_value", fiscal_document_line.insurance_value),
            SQL("%s AS other_value", fiscal_document_line.other_value),
            SQL("%s AS discount_value", fiscal_document_line.discount_value),
        ]
