# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# Copyright (C) 2021 - TODAY Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models
from odoo.tools import SQL

from odoo.addons.l10n_br_fiscal.constants.fiscal import PRODUCT_FISCAL_TYPE


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
    )

    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
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

    def _select_list(self, table):
        values = (
            "ipi_value",
            "icmsst_value",
            "freight_value",
            "insurance_value",
            "other_value",
        )
        return [
            *super()._select_list(table),
            table.fiscal_operation_id,
            table.fiscal_operation_line_id,
            table.cfop_id,
            table.fiscal_type,
            table.ncm_id,
            table.nbm_id,
            table.cest_id,
            SQL("SUM(%s) AS icms_value", table.icms_value),
            SQL("SUM(%s) AS icmsst_value", table.icmsst_value),
            SQL("SUM(%s) AS ipi_value", table.ipi_value),
            SQL("SUM(%s) AS pis_value", table.pis_value),
            SQL("SUM(%s) AS cofins_value", table.cofins_value),
            SQL("SUM(%s) AS ii_value", table.ii_value),
            SQL("SUM(%s) AS freight_value", table.freight_value),
            SQL("SUM(%s) AS insurance_value", table.insurance_value),
            SQL("SUM(%s) AS other_value", table.other_value),
            SQL(
                "SUM(%s / COALESCE(NULLIF(%s, 0), 1.0) * %s)::decimal(16,2) + %s"
                " AS total_with_taxes",
                table.price_unit,
                table.order_id.currency_rate,
                table.product_qty,
                SQL(" + ").join(
                    SQL("SUM(COALESCE(%s, 0.0))", table[value]) for value in values
                ),
            ),
        ]

    def _groupby_list(self, table):
        return [
            *super()._groupby_list(table),
            table.fiscal_operation_id,
            table.fiscal_operation_line_id,
            table.cfop_id,
            table.fiscal_type,
            table.ncm_id,
            table.nbm_id,
            table.cest_id,
        ]
