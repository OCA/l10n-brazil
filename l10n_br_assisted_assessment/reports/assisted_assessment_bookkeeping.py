# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    FISCAL_OUT,
    SITUACAO_EDOC_AUTORIZADA,
)

from ..constants import (
    BOOKKEEPING_STATUSES,
    LINE_CREDIT,
    LINE_DEBIT,
    LINE_TYPES,
)


class AssistedAssessmentBookkeepingLine(models.Model):
    _name = "l10n_br_assisted_assessment.bookkeeping.line"
    _description = "ERP document expected in the assisted assessment"
    _auto = False
    _order = "line_type, document_key, id"

    period_id = fields.Many2one(
        comodel_name="l10n_br_assisted_assessment.period",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="period_id.company_id")
    currency_id = fields.Many2one(related="period_id.currency_id")
    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        required=True,
    )
    document_key = fields.Char(string="Access Key")
    line_type = fields.Selection(selection=LINE_TYPES, required=True)
    expected_value = fields.Monetary(
        compute="_compute_bookkeeping_values",
        help="CBS or IBS booked on the authorized fiscal document.",
    )
    fisco_value = fields.Monetary(
        string="Assessed Value",
        compute="_compute_bookkeeping_values",
    )
    status = fields.Selection(
        selection=BOOKKEEPING_STATUSES,
        compute="_compute_bookkeeping_values",
    )

    def init(self):
        # Drop a leftover Transient table or a previous view of the same name.
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"DROP TABLE IF EXISTS {self._table} CASCADE")
        self.env.cr.execute(
            f"CREATE OR REPLACE VIEW {self._table} AS ({self._query()})"
        )

    def _query(self):
        """One row per authorized document of each period, in Brasília time."""
        return f"""
            SELECT
                (p.id::bigint * 1000000000 + d.id::bigint) AS id,
                p.id AS period_id,
                d.id AS document_id,
                d.document_key AS document_key,
                CASE
                    WHEN d.fiscal_operation_type = '{FISCAL_OUT}'
                    THEN '{LINE_DEBIT}'
                    ELSE '{LINE_CREDIT}'
                END AS line_type
            FROM l10n_br_assisted_assessment_period p
            JOIN l10n_br_fiscal_document d
                ON d.company_id = p.company_id
                AND d.state_edoc = '{SITUACAO_EDOC_AUTORIZADA}'
                AND NULLIF(d.document_key, '') IS NOT NULL
                AND d.document_date >= p.document_utc_from
                AND d.document_date < p.document_utc_to
            WHERE p.document_utc_from IS NOT NULL
              AND p.document_utc_to IS NOT NULL
        """

    @api.depends(
        "period_id.tribute",
        "period_id.line_ids.value",
        "period_id.line_ids.document_key",
        "period_id.line_ids.line_type",
        "period_id.no_debits",
        "period_id.no_credits",
        "document_id.fiscal_line_ids",
        "line_type",
    )
    def _compute_bookkeeping_values(self):
        pending = self
        for period in self.period_id:
            assessed = period._assessed_values_by_key()
            compared = period._compared_line_types()
            value_field = f"{period.tribute}_value"
            period_lines = pending.filtered(
                lambda rec, current=period: rec.period_id == current
            )
            for line in period_lines:
                expected = sum(line.document_id.fiscal_line_ids.mapped(value_field))
                fisco_entry = assessed.get(
                    (line.line_type, line.document_id.document_key)
                )
                fisco_value = fisco_entry["value"] if fisco_entry else None
                line.expected_value = expected
                line.fisco_value = fisco_value or 0.0
                line.status = period._bookkeeping_status(
                    line.line_type, expected, fisco_value, compared
                )
            pending -= period_lines
        for line in pending:
            line.expected_value = 0.0
            line.fisco_value = 0.0
            line.status = False
