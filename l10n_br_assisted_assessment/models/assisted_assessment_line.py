# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

from ..constants import DEBIT_ORIGINS, DOCUMENT_KEY_SIZE, DOCUMENT_MODELS, LINE_TYPES


class AssistedAssessmentLine(models.Model):
    _name = "l10n_br_assessment.line"
    _description = "IBS/CBS assisted assessment line"
    _order = "period_id, line_type, document_key, origin"

    period_id = fields.Many2one(
        comodel_name="l10n_br_assessment.period",
        string="Period",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="period_id.company_id", store=True)
    currency_id = fields.Many2one(related="period_id.currency_id", store=True)
    line_type = fields.Selection(selection=LINE_TYPES, required=True)
    document_key = fields.Char(
        string="Access Key",
        size=DOCUMENT_KEY_SIZE,
        index=True,
        help="Access key of the electronic document that produced the value.",
    )
    origin = fields.Integer(
        default=0,
        help="Origin reported by the tax administration. The same document can "
        "produce more than one line, such as a normal debit and a debit note.",
    )
    origin_name = fields.Char(compute="_compute_origin_name")
    document_model = fields.Integer()
    document_model_name = fields.Char(compute="_compute_document_model_name")
    date_emission = fields.Datetime(string="Emission")
    date_registration = fields.Datetime(string="Registration")
    date_update = fields.Datetime(string="Last Update")

    value = fields.Monetary(
        string="Assessed Value",
        help="Value assessed by the tax administration, compared against the "
        "bookkeeping during the reconciliation.",
    )
    value_excess = fields.Monetary(
        string="Excess",
        help="Value reported as not processed by the tax administration.",
    )
    value_suspended = fields.Monetary(string="Suspended")
    value_balance = fields.Monetary(
        string="Remaining Balance",
        help="Payable balance for debits and creditable balance for credits.",
    )
    value_detail = fields.Json(
        string="Value Breakdown",
        help="Full value group as delivered by the tax administration, kept for "
        "auditing the figures that are not modelled as fields.",
    )

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        help="Booked document matched by access key.",
    )
    divergence_ids = fields.One2many(
        comodel_name="l10n_br_assessment.divergence",
        inverse_name="line_id",
    )

    @api.depends("line_type", "document_key")
    def _compute_display_name(self):
        line_types = dict(self._fields["line_type"]._description_selection(self.env))
        for line in self:
            line.display_name = " ".join(
                part
                for part in (line_types.get(line.line_type), line.document_key)
                if part
            ) or _("New")

    @api.depends("origin", "line_type")
    def _compute_origin_name(self):
        for line in self:
            line.origin_name = DEBIT_ORIGINS.get(line.origin) or str(line.origin)

    @api.depends("document_model")
    def _compute_document_model_name(self):
        for line in self:
            line.document_model_name = DOCUMENT_MODELS.get(line.document_model) or ""

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._match_document()
        return lines

    def _match_document(self):
        documents = self.env["l10n_br_fiscal.document"]
        for line in self:
            document = documents.browse()
            if line.document_key:
                document = documents.search(
                    [
                        ("document_key", "=", line.document_key),
                        ("company_id", "=", line.period_id.company_id.id),
                    ],
                    limit=1,
                )
            line.document_id = document
        return True

    def _natural_key(self):
        """Key used to update a line the tax administration sent again.

        The assessment APIs deliver increments, so a line already stored must be
        updated instead of duplicated.
        """
        self.ensure_one()
        return (self.line_type, self.document_key, self.origin)

    def _values_changed(self, vals):
        """Return whether ``vals`` would change a stored increment."""
        self.ensure_one()
        for field_name, value in vals.items():
            if field_name in ("period_id", "line_type"):
                continue
            current = self[field_name]
            if current != value and (current or value):
                return True
        return False
