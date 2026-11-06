# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import calendar
from datetime import date, timedelta

from odoo import api, fields, models

from ..constants import REINF_DARF_DUE_DAY, REINF_DARF_MINIMUM, REINF_DARF_STATES

SATURDAY = 5

# A run of non business days longer than this does not exist in the Brazilian
# calendar, and the bound keeps a misconfigured calendar from looping forever.
MAX_ANTICIPATION_DAYS = 10


class ReinfDarf(models.Model):
    """The mirror of a DARF, for conference and for provisioning.

    It never issues a collection document, and that is a deliberate
    repositioning: since the competence 01/2024 the numbered DARF is issued by
    the DCTFWeb after the closing of the EFD-Reinf, and a DARF issued on the
    side creates a payment with no debt attached to it. So this model exists to
    answer three questions: how much is due per revenue code, whether it matches
    what the DCTFWeb says, and what happens to the balance that is too small to
    be collected.

    That last one is not a detail: by the art. 68 of the Law 9.430/1996 a
    balance below the minimum is NOT collected and travels to the next
    competence under the SAME revenue code, so it is state that crosses
    competences and it needs a record of its own.
    """

    _name = "l10n_br_reinf.darf"
    _description = "EFD-Reinf DARF Mirror"
    _order = "period desc, revenue_code"
    _rec_name = "revenue_code"

    calculation_id = fields.Many2one(
        comodel_name="l10n_br_reinf.calculation",
        string="Calculation",
        required=True,
        index=True,
        ondelete="cascade",
    )

    company_id = fields.Many2one(
        related="calculation_id.company_id",
        store=True,
        index=True,
    )

    currency_id = fields.Many2one(
        related="company_id.currency_id",
    )

    period = fields.Char(
        related="calculation_id.period",
        store=True,
        index=True,
    )

    revenue_code = fields.Char(
        size=6,
        required=True,
        index=True,
        help="Revenue code (CR) of the collection, as the Annex I gives it.",
    )

    amount = fields.Monetary(
        string="Amount of the Competence",
        currency_field="currency_id",
    )

    carried_amount = fields.Monetary(
        string="Carried In",
        currency_field="currency_id",
        help="Balance of previous competences that was below the minimum and "
        "travelled to this one, under the same revenue code.",
    )

    total_amount = fields.Monetary(
        string="Total",
        compute="_compute_total_amount",
        store=True,
        currency_field="currency_id",
    )

    carried_from_id = fields.Many2one(
        comodel_name="l10n_br_reinf.darf",
        string="Carried From",
        readonly=True,
        help="The DARF of the previous competence whose balance came here.",
    )

    carried_to_ids = fields.One2many(
        comodel_name="l10n_br_reinf.darf",
        inverse_name="carried_from_id",
        string="Carried To",
    )

    due_date = fields.Date(
        help="Second ten-day period of the month after the competence, "
        "anticipated when it falls on a weekend.",
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_reinf.calculation.line",
        inverse_name="darf_id",
        string="Lines",
        readonly=True,
    )

    dctfweb_darf_number = fields.Char(
        string="DCTFWeb DARF Number",
        help="Number of the DARF the DCTFWeb issued, written here by hand: it "
        "is the third leg of the conference.",
    )

    dctfweb_amount = fields.Monetary(
        string="DCTFWeb Amount",
        currency_field="currency_id",
        help="Amount of the DARF issued by the DCTFWeb, for the confrontation.",
    )

    dctfweb_difference = fields.Monetary(
        string="Difference",
        compute="_compute_dctfweb_difference",
        store=True,
        currency_field="currency_id",
    )

    state = fields.Selection(
        selection=REINF_DARF_STATES,
        default="draft",
        required=True,
        index=True,
        readonly=True,
        copy=False,
    )

    @api.depends("amount", "carried_amount")
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.amount + record.carried_amount

    @api.depends("total_amount", "dctfweb_amount")
    def _compute_dctfweb_difference(self):
        for record in self:
            record.dctfweb_difference = (
                record.dctfweb_amount - record.total_amount
                if record.dctfweb_amount
                else 0.0
            )

    @api.model
    def _due_date_of(self, period, company=None):
        """Due date of a competence: day 20 of the month after it.

        A due date that is not a banking business day is ANTICIPATED, never
        postponed. The holidays come from the calendar of the company, through
        l10n_br_resource, which is what knows the national banking holidays;
        with no calendar configured only the weekend is avoided, and the
        difference is visible instead of silent.
        """
        year, month = (int(part) for part in period.split("-"))
        month += 1
        if month > 12:
            month, year = 1, year + 1
        day = min(REINF_DARF_DUE_DAY, calendar.monthrange(year, month)[1])
        due = date(year, month, day)
        resource_calendar = (company or self.env.company).resource_calendar_id
        for _attempt in range(MAX_ANTICIPATION_DAYS):
            if resource_calendar:
                if resource_calendar.data_eh_dia_util_bancario(due):
                    return due
            elif due.weekday() < SATURDAY:
                return due
            due -= timedelta(days=1)
        return due

    def _is_below_minimum(self):
        self.ensure_one()
        return self.total_amount < REINF_DARF_MINIMUM
