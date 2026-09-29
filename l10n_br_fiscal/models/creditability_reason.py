# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

CREDITABILITY_REASON_KIND = [
    ("benefit", "Tax benefit conditioned on waiving the credit"),
    ("court_decision", "Court decision"),
    ("special_regime", "State special regime"),
    ("assessment", "Tax authority ruling"),
    ("other", "Other, described in the legal basis"),
]


class CreditabilityReason(models.Model):
    """Why a line departs from the derived creditability.

    The user never types a cost. When a line must not follow the rule, the
    user picks the reason from this closed list and the system recomputes.
    A cost that cannot be rebuilt from the invoice plus the configuration
    cannot be defended in an audit, so the freedom belongs to the
    justification and never to the arithmetic.

    Every reason carries its legal basis, which is what separates a fiscal
    criterion from a free text tag.
    """

    _name = "l10n_br_fiscal.creditability.reason"
    _description = "Creditability Reason"
    _order = "code, name"

    code = fields.Char(required=True, index=True)

    name = fields.Char(required=True, index=True)

    kind = fields.Selection(
        selection=CREDITABILITY_REASON_KIND,
        required=True,
        default="other",
    )

    legal_basis = fields.Char(
        required=True,
        help="The rule, court case or special regime number that supports"
        " departing from the derived creditability. Required: a fiscal"
        " criterion without a legal ground is not auditable.",
    )

    date_start = fields.Date(
        help="First day this reason may be applied. Empty means no start" " limit.",
    )

    date_end = fields.Date(
        help="Last day this reason may be applied. Empty means it is still"
        " in force.",
    )

    active = fields.Boolean(default=True)

    notes = fields.Text()

    _sql_constraints = [
        (
            "l10n_br_fiscal_creditability_reason_code_uniq",
            "unique (code)",
            _("Creditability reason already exists with this code !"),
        )
    ]

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end:
                if record.date_end < record.date_start:
                    raise ValidationError(
                        _("The end date cannot be earlier than the start date.")
                    )

    def _is_in_force(self, date):
        """Whether this reason may be applied on ``date``."""
        self.ensure_one()
        if self.date_start and date and date < self.date_start:
            return False
        if self.date_end and date and date > self.date_end:
            return False
        return True

    def name_get(self):
        return [(record.id, f"[{record.code}] {record.name}") for record in self]
