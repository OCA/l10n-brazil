# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models

from ..constants import REINF_EXCEPTION_CRITICAL, REINF_EXCEPTION_REASONS

# What to do about each reason. A screen that says "there is a problem" without
# saying what to do is a screen nobody uses.
EXCEPTION_ADVICE = {
    "partner_without_cnpj": "Fill the CNPJ or the CPF of the beneficiary: the "
    "event identifies it by the inscription.",
    "nature_missing": "Set the nature of income on the service type, on the "
    "partner or on the line itself.",
    "partial_payment": "Only the paid share is declared in this competence. "
    "Check the remaining balance in the next one.",
    "advance_payment": "An advance has no invoice to take the nature from: "
    "reconcile it or declare it by hand.",
    "cancelled_after_payment": "The invoice was cancelled after being paid. "
    "Decide between rectifying and excluding the event of the competence.",
    "prior_period_invoice": "The credit is of another competence and only the "
    "PCC lands here. This is the rule, not an error.",
    "payment_without_invoice": "Reconcile the payment with the invoice, or "
    "declare it by hand if there is really no document.",
    "simples_beneficiary": "A beneficiary under the Simples Nacional suffers "
    "no PCC. The income is written with the withholding in blank.",
    "cooperative_csll_only": "CSLL is waived for a cooperative. PIS/PASEP and "
    "COFINS go under their own revenue codes, never aggregated.",
    "below_minimum": "The total of the revenue code stays below the minimum to "
    "COLLECT (art. 68 of the Law 9.430/1996) and is carried to the next "
    "competence under the same code. It does not undo the withholding.",
    "judicial_suspension": "The withholding is suspended by a decision: the "
    "process has to be declared in the R-1070 first.",
}


class ReinfCalculationException(models.Model):
    """Something that is not a plain declaration line, with its reason named.

    This model is what makes the conference screen worth opening. Every reason
    is enumerated, points at the record it came from and carries what to do
    about it. A critical one blocks the closing of the competence.
    """

    _name = "l10n_br_reinf.calculation.exception"
    _description = "EFD-Reinf Calculation Exception"
    _order = "critical desc, reason, id"

    calculation_id = fields.Many2one(
        comodel_name="l10n_br_reinf.calculation",
        string="Calculation",
        required=True,
        index=True,
        ondelete="cascade",
    )

    reason = fields.Selection(
        selection=REINF_EXCEPTION_REASONS,
        required=True,
        index=True,
    )

    critical = fields.Boolean(
        compute="_compute_critical",
        store=True,
        help="A critical exception blocks the closing of the competence.",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Beneficiary",
        index=True,
    )

    source_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Source Invoice",
        index=True,
        ondelete="cascade",
    )

    source_move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Source Line",
        index=True,
        ondelete="cascade",
    )

    amount = fields.Monetary(
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        related="calculation_id.company_id.currency_id",
    )

    advice = fields.Char(
        compute="_compute_advice",
        help="What to do about it.",
    )

    note = fields.Char()

    ignored = fields.Boolean(
        readonly=True,
        copy=False,
        help="Somebody decided this one does not block the competence.",
    )

    ignored_reason = fields.Char(
        readonly=True,
        copy=False,
    )

    @api.depends("reason", "ignored")
    def _compute_critical(self):
        for record in self:
            record.critical = (
                record.reason in REINF_EXCEPTION_CRITICAL and not record.ignored
            )

    @api.depends("reason")
    def _compute_advice(self):
        for record in self:
            record.advice = EXCEPTION_ADVICE.get(record.reason, "")

    def action_open_source(self):
        """Open the record the exception came from."""
        self.ensure_one()
        record = self.source_move_id or self.partner_id
        if not record:
            return False
        return {
            "type": "ir.actions.act_window",
            "res_model": record._name,
            "res_id": record.id,
            "view_mode": "form",
        }

    def _log_ignored(self):
        for record in self:
            record.calculation_id.message_post(
                body=_(
                    "Exception %(reason)s of %(partner)s ignored: %(note)s",
                    reason=dict(REINF_EXCEPTION_REASONS).get(record.reason),
                    partner=record.partner_id.display_name or "-",
                    note=record.ignored_reason or "-",
                )
            )
        return True
