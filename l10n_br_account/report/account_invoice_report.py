# Copyright (C) 2016-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
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

    @api.model
    def _select(self):
        # same sign and currency rate the core applies to price_subtotal and
        # price_total: refunds and vendor bills are negative
        factor = (
            "(CASE WHEN move.move_type IN ('in_invoice', 'out_refund', 'in_receipt')"
            " THEN -1 ELSE 1 END) * account_currency_table.rate"
        )
        res = self._fiscal_report_select(
            "fdl", "partner", factor=factor, aggregate=False
        )
        res.update(
            {
                "partner_state_id": (
                    "COALESCE(partner.state_id, commercial_partner.state_id)"
                ),
                "issuer": "fd.issuer",
                "document_type_id": "fd.document_type_id",
                "document_serie_id": "fd.document_serie_id",
                "state_edoc": "fd.state_edoc",
            }
        )
        fiscal = "".join(f", {expr} AS {fname}" for fname, expr in res.items())
        return SQL("%s" + fiscal, super()._select())

    @api.model
    def _from(self):
        joins = (
            " LEFT JOIN l10n_br_fiscal_document fd"
            " ON fd.id = move.fiscal_document_id"
            " LEFT JOIN l10n_br_fiscal_document_line fdl"
            " ON fdl.id = line.fiscal_document_line_id"
        )
        return SQL("%s" + joins + self._fiscal_report_from("fdl"), super()._from())
