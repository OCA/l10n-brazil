# Copyright (C) 2016-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import SQL

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER,
    SITUACAO_EDOC,
)


class AccountInvoiceReport(models.Model):
    _name = "account.invoice.report"
    _inherit = ["account.invoice.report", "l10n_br_fiscal.report.mixin"]

    issuer = fields.Selection(
        selection=DOCUMENT_ISSUER,
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        string="Fiscal Document Type",
    )

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
    )

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string="Situation",
    )

    def _select_list(self, table):
        """Add the Brazilian fiscal columns to the invoice statistics.

        Odoo 20.0 builds the report with the TableSQL API: the fiscal
        document (line) is joined explicitly through its fields instead of
        the removed _select()/_from() string hooks of 19.0. Every dimension
        declared by ``l10n_br_fiscal.report.mixin`` has to be selected here,
        otherwise the model fields have no column in the report.
        """
        # account.move.line -> fiscal line, account.move -> fiscal document:
        # TableSQL joins the tables as the columns are used
        document = table.move_id.fiscal_document_id
        fiscal_line = table.fiscal_document_line_id
        columns = {
            "issuer": document.issuer,
            "document_type_id": document.document_type_id,
            "document_serie_id": document.document_serie_id,
            "state_edoc": document.state_edoc,
            "fiscal_operation_type": (
                fiscal_line.fiscal_operation_id.fiscal_operation_type
            ),
            "cfop_destination": fiscal_line.cfop_id.destination,
            "partner_state_id": table.partner_id.state_id,
        }
        for fname in (
            "fiscal_operation_id",
            "fiscal_operation_line_id",
            "cfop_id",
            "ncm_id",
            "nbm_id",
            "cest_id",
            "nbs_id",
            "fiscal_type",
            "fiscal_genre_id",
            "service_type_id",
            "icms_cst_id",
            "icms_origin",
            "ind_final",
            "tax_icms_or_issqn",
            "tax_classification_id",
        ):
            columns[fname] = fiscal_line[fname]
        # every measure the fiscal report mixin reads from the fiscal line,
        # with the sign the core gives to price_subtotal (refunds and vendor
        # bills are negative)
        in_out_sign = SQL(
            "CASE WHEN %s IN ('in_invoice', 'out_refund', 'in_receipt')"
            " THEN -1 ELSE 1 END",
            table.move_id.move_type,
        )
        for fname in self._fiscal_report_measures():
            columns[fname] = SQL("%s * %s", fiscal_line[fname], in_out_sign)
        return super()._select_list(table) + [
            SQL("%s AS %s", expr, SQL.identifier(fname))
            for fname, expr in columns.items()
        ]
