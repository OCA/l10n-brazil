# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import _, api, fields, models
from odoo.tools.misc import format_date, formatLang


class TaxAssessment(models.Model):
    _inherit = "l10n_br_tax.assessment"

    opening_balance_warning = fields.Char(
        string="Aviso do saldo inicial",
        compute="_compute_opening_balance_warning",
        help="Aviso quando o saldo contábil de impostos a recuperar antes do "
        "período não é o saldo inicial de crédito informado.",
    )

    def _opening_balances(self):
        """The opening balance of the credit that the first assessment of the
        company starts from."""
        self.ensure_one()
        return self.env["l10n_br_pis_cofins.credit.opening"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("tax_domain", "=", self.tax_domain),
                ("cutoff_date", "<=", self.date_from),
            ]
        )

    def _is_pis_cofins_non_cumulative(self):
        self.ensure_one()
        return self.regime == "non_cumulative" and self.tax_domain in ("pis", "cofins")

    def _get_opening_balance(self):
        self.ensure_one()
        if self._is_pis_cofins_non_cumulative():
            return round(sum(self._opening_balances().mapped("balance")), 2)
        return super()._get_opening_balance()

    def _get_first_period_date(self):
        """The movement before the cut-off of an opening balance belongs to the
        previous system: the months that count start at the cut-off."""
        self.ensure_one()
        if self._is_pis_cofins_non_cumulative():
            openings = self._opening_balances()
            if openings:
                return min(openings.mapped("cutoff_date"))
        return super()._get_first_period_date()

    @api.depends(
        "state", "previous_assessment_id", "previous_balance", "date_from", "company_id"
    )
    def _compute_opening_balance_warning(self):
        """The system books no entry for the opening balance: the balance of the
        taxes to recover is already in the opening balance sheet. When the
        account of the tax to recover does not hold what was informed as the
        opening balance of the credit, the assessment says so (it never blocks)."""
        for record in self:
            record.opening_balance_warning = False
            if (
                not record._is_pis_cofins_non_cumulative()
                or record.previous_assessment_id
                or not record.date_from
            ):
                continue
            openings = record._opening_balances()
            start = record.company_id.tax_assessment_start
            if openings and start and start != min(openings.mapped("cutoff_date")):
                # one source only: the cut-off of the opening balance rules
                record.opening_balance_warning = _(
                    "The start of the assessment of the company (%(start)s) is not "
                    "the cut-off of the opening balance of the credit (%(cutoff)s): "
                    "the cut-off of the opening balance is the one that counts for "
                    "the PIS and the COFINS.",
                    start=format_date(self.env, start),
                    cutoff=format_date(self.env, min(openings.mapped("cutoff_date"))),
                )
                continue
            account = record.tax_group_id.with_company(
                record.company_id
            ).property_tax_receivable_account_id
            if not openings or not account:
                continue
            lines = (
                self.env["account.move.line"]
                .sudo()
                .search(
                    [
                        ("account_id", "=", account.id),
                        ("company_id", "=", record.company_id.id),
                        ("parent_state", "=", "posted"),
                        ("date", "<", record.date_from),
                    ]
                )
            )
            ledger = round(sum(lines.mapped("balance")), 2)
            opening = round(sum(openings.mapped("balance")), 2)
            if abs(ledger - opening) > 0.01:
                record.opening_balance_warning = _(
                    "The balance of the account %(account)s before the period "
                    "(%(ledger)s) is not the opening balance of the credit "
                    "(%(opening)s). The system books no entry for the opening "
                    "balance: check the opening balance sheet.",
                    account=account.display_name,
                    ledger=formatLang(self.env, ledger, digits=2),
                    opening=formatLang(self.env, opening, digits=2),
                )
