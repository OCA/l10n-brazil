# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    ACTION_DEBIT_NOTE,
    ACTION_FIX_REGISTRATION,
    ACTION_REGISTER_DOCUMENT,
    ACTION_REVIEW_CREDIT,
    DIVERGENCE_CREDIT_DENIED,
    DIVERGENCE_MISSING_FISCO,
    DIVERGENCE_MISSING_LOCAL,
    DIVERGENCE_TYPES,
    DIVERGENCE_VALUE,
    DOCUMENT_KEY_SIZE,
    LINE_CREDIT,
    LINE_DEBIT,
    LINE_TYPES,
    SUGGESTED_ACTIONS,
)


class AssistedAssessmentDivergence(models.Model):
    _name = "l10n_br_assessment.divergence"
    _description = "IBS/CBS assisted assessment divergence"
    _order = "period_id, divergence_type, document_key"

    period_id = fields.Many2one(
        comodel_name="l10n_br_assessment.period",
        string="Period",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="period_id.company_id", store=True)
    currency_id = fields.Many2one(related="period_id.currency_id", store=True)
    line_id = fields.Many2one(
        comodel_name="l10n_br_assessment.line",
        string="Line",
        ondelete="set null",
    )
    divergence_type = fields.Selection(selection=DIVERGENCE_TYPES, required=True)
    line_type = fields.Selection(selection=LINE_TYPES, required=True)
    document_key = fields.Char(string="Access Key", size=DOCUMENT_KEY_SIZE, index=True)
    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
    )
    fisco_value = fields.Monetary(string="Assessed Value")
    local_value = fields.Monetary(string="Booked Value")
    difference = fields.Monetary(compute="_compute_difference", store=True)
    suggested_action = fields.Selection(selection=SUGGESTED_ACTIONS)
    notes = fields.Text(
        help="Required when the divergence is ignored, so the reason for "
        "accepting the tax administration figure stays on the record.",
    )
    state = fields.Selection(
        selection=[
            ("open", "Open"),
            ("handled", "Handled"),
            ("ignored", "Ignored"),
        ],
        string="Status",
        default="open",
        required=True,
    )

    @api.depends("fisco_value", "local_value")
    def _compute_difference(self):
        for record in self:
            record.difference = record.fisco_value - record.local_value

    @api.depends("divergence_type", "document_key")
    def _compute_display_name(self):
        types = dict(self._fields["divergence_type"]._description_selection(self.env))
        for record in self:
            record.display_name = " ".join(
                part
                for part in (types.get(record.divergence_type), record.document_key)
                if part
            ) or _("New")

    @api.model
    def _prepare_vals(
        self,
        period,
        divergence_type,
        line_type,
        document_key,
        fisco_value,
        local_value,
        line=None,
    ):
        document = (
            line.document_id if line else self._find_document(period, document_key)
        )
        return {
            "period_id": period.id,
            "line_id": line.id if line else False,
            "divergence_type": divergence_type,
            "line_type": line_type,
            "document_key": document_key,
            "document_id": document.id,
            "fisco_value": fisco_value,
            "local_value": local_value,
            "suggested_action": self._suggested_action(
                divergence_type, line_type, fisco_value, local_value
            ),
        }

    @api.model
    def _find_document(self, period, document_key):
        return self.env["l10n_br_fiscal.document"].search(
            [
                ("document_key", "=", document_key),
                ("company_id", "=", period.company_id.id),
            ],
            limit=1,
        )

    @api.model
    def _suggested_action(self, divergence_type, line_type, fisco_value, local_value):
        """Return the action that repairs the divergence.

        Adjustments are made by issuing fiscal documents, so a value the fisco
        did not charge becomes a debit note, while a wrongly charged value is
        repaired at the source, in the tax registration that produced the XML.
        """
        if divergence_type == DIVERGENCE_MISSING_LOCAL:
            return ACTION_REGISTER_DOCUMENT
        if divergence_type == DIVERGENCE_CREDIT_DENIED:
            return ACTION_REVIEW_CREDIT
        if divergence_type == DIVERGENCE_MISSING_FISCO:
            return (
                ACTION_DEBIT_NOTE if line_type == LINE_DEBIT else ACTION_REVIEW_CREDIT
            )
        if divergence_type == DIVERGENCE_VALUE:
            if line_type == LINE_CREDIT:
                return ACTION_REVIEW_CREDIT
            return (
                ACTION_DEBIT_NOTE
                if local_value > fisco_value
                else ACTION_FIX_REGISTRATION
            )
        return False

    def _natural_key(self):
        """Key used to reuse a treated divergence on a later reconciliation."""
        self.ensure_one()
        return (self.line_type, self.document_key, self.divergence_type)

    def _values_changed(self, vals):
        """Return whether ``vals`` would change a stored divergence."""
        self.ensure_one()
        for field_name, value in vals.items():
            if field_name in ("period_id", "state"):
                continue
            current = self[field_name]
            if self._fields[field_name].type == "many2one":
                current = current.id if current else False
            if current != value and (current or value):
                return True
        return False

    def write(self, vals):
        result = super().write(vals)
        if vals.get("state") == "handled":
            self._check_handled()
        if vals.get("state") == "ignored":
            self._check_ignored()
        return result

    def action_mark_handled(self):
        return self.write({"state": "handled"})

    def action_mark_ignored(self):
        return self.write({"state": "ignored"})

    def _check_handled(self):
        """A missing local document is handled by registering that document."""
        for record in self:
            if record.divergence_type != DIVERGENCE_MISSING_LOCAL:
                continue
            if not record.document_id:
                raise UserError(
                    _(
                        "Link the fiscal document that registers this access "
                        "key before marking the divergence as handled."
                    )
                )
            if (
                record.document_key
                and record.document_id.document_key
                and record.document_key != record.document_id.document_key
            ):
                raise UserError(
                    _(
                        "The fiscal document access key does not match the "
                        "assessment line."
                    )
                )

    def _check_ignored(self):
        for record in self:
            if (record.notes or "").strip():
                continue
            raise UserError(
                _(
                    "Explain why this divergence is ignored before confirming "
                    "the assessment without fixing it."
                )
            )
