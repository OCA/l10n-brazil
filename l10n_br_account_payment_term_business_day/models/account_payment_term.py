# Copyright (C) 2026 - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.exceptions import ValidationError

BUSINESS_DAY_POLICIES = [
    ("none", "No shift"),
    ("next", "Postpone to the next business day"),
    ("previous", "Anticipate to the previous business day"),
]


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    business_day_policy = fields.Selection(
        selection=BUSINESS_DAY_POLICIES,
        string="Business Day",
        default="none",
        required=True,
        help=(
            "What to do when the due date falls on a day the banks do not settle. "
            "The direction belongs to the tax, not to the supplier: a DARF anticipates "
            "and an ICMS payment slip postpones, so each one gets its own payment term."
        ),
    )
    holiday_calendar_id = fields.Many2one(
        comodel_name="resource.calendar",
        string="Holiday Calendar",
        help=(
            "Calendar that decides which days the banks are closed. It stacks with its "
            "parents, so a municipal calendar already carries the state and national "
            "holidays."
        ),
    )

    @api.constrains("business_day_policy", "holiday_calendar_id")
    def _check_holiday_calendar(self):
        for term in self:
            if term.business_day_policy != "none" and not term.holiday_calendar_id:
                raise ValidationError(
                    self.env._(
                        "Payment term %(term)s shifts the due date to a business day "
                        "but has no holiday calendar: without one only weekends would "
                        "be skipped, and a holiday would silently stay as a due date.",
                        term=term.display_name,
                    )
                )

    def _shift_to_business_day(self, due_date):
        """Move a due date off a non-banking day, in the term's direction.

        The banking calendar is used, not the labour one: Carnival and Corpus Christi
        are ``B`` leaves, which are working days for the company and still settle
        nothing. A date that already is a banking business day is returned untouched —
        ``next_bank_business_day`` and ``previous_bank_business_day`` are strictly
        after and before, so they cannot be used for normalization.
        """
        self.ensure_one()
        calendar = self.holiday_calendar_id
        if self.business_day_policy == "none" or not calendar or not due_date:
            return due_date
        if calendar.is_bank_business_day(due_date):
            return due_date
        if self.business_day_policy == "next":
            shifted = calendar.next_bank_business_day(due_date)
        else:
            shifted = calendar.previous_bank_business_day(due_date)
        return shifted.date() if hasattr(shifted, "date") else shifted

    def _compute_terms(
        self,
        date_ref,
        currency,
        company,
        tax_amount,
        tax_amount_currency,
        sign,
        untaxed_amount,
        untaxed_amount_currency,
        cash_rounding=None,
    ):
        # After super(), never instead of it: the instalments and the amounts stay
        # with the core computation and any other module that changes the due date
        # keeps working. Only the date of each instalment is shifted here.
        result = super()._compute_terms(
            date_ref,
            currency,
            company,
            tax_amount,
            tax_amount_currency,
            sign,
            untaxed_amount,
            untaxed_amount_currency,
            cash_rounding=cash_rounding,
        )
        if self.business_day_policy == "none":
            return result
        for term_vals in result.get("line_ids", []):
            term_vals["date"] = self._shift_to_business_day(term_vals.get("date"))
        return result
