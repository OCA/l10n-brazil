# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import calendar
import logging
from collections import defaultdict
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import (
    REINF_AGGREGATABLE_TAXES,
    REINF_CALCULATION_STATES,
    REINF_TAX_DOMAIN_MAP,
    REINF_TAXES_ON_CREDIT,
    REINF_WITHHOLDING_SOURCES,
    REINF_WITHHOLDING_TAXES,
)
from .reinf_event import PERIOD_RE

_logger = logging.getLogger(__name__)

SUPPLIER_MOVE_TYPES = ("in_invoice", "in_refund")


class ReinfCalculation(models.Model):
    """The calculation of one competence of one company.

    Where the data comes from is a decision, not an accident: the declaration
    is born from the PAYMENT and from the CREDIT, never from the withholding
    invoices the accounting generates. Two reasons. First, income with no
    withholding also has to be declared (dividends that are exempt, a
    withholding waived for being below the minimum is written with the value in
    blank), and a withholding invoice does not exist for those. Second, the
    taxable event is per tax, so the same invoice feeds two different
    competences, which a per-invoice reading cannot express.

    The withholding invoices and the tax lines are still read, but as something
    to be RECONCILED against, and the difference shows up in the conference
    screen instead of being averaged away.
    """

    _name = "l10n_br_reinf.calculation"
    _inherit = ["mail.thread"]
    _description = "EFD-Reinf Calculation"
    _order = "period desc, company_id"
    _rec_name = "period"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    currency_id = fields.Many2one(
        related="company_id.currency_id",
    )

    period = fields.Char(
        string="Competence",
        size=7,
        required=True,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Competence of the calculation, as AAAA-MM.",
    )

    state = fields.Selection(
        selection=REINF_CALCULATION_STATES,
        default="draft",
        required=True,
        index=True,
        readonly=True,
        copy=False,
        tracking=True,
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_reinf.calculation.line",
        inverse_name="calculation_id",
        string="Lines",
    )

    exception_ids = fields.One2many(
        comodel_name="l10n_br_reinf.calculation.exception",
        inverse_name="calculation_id",
        string="Exceptions",
    )

    darf_ids = fields.One2many(
        comodel_name="l10n_br_reinf.darf",
        inverse_name="calculation_id",
        string="DARFs",
        readonly=True,
    )

    event_ids = fields.One2many(
        comodel_name="l10n_br_reinf.event",
        inverse_name="calculation_id",
        string="Events",
        readonly=True,
    )

    # Stored totals: an industrial competence has thousands of lines and the
    # conference screen is opened over and over.
    line_count = fields.Integer(
        compute="_compute_totals",
        store=True,
    )

    total_base_amount = fields.Monetary(
        string="Total Base",
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )

    total_wh_amount = fields.Monetary(
        string="Total Withheld",
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )

    total_divergence_amount = fields.Monetary(
        string="Total Divergence",
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )

    exception_count = fields.Integer(
        compute="_compute_exception_counts",
        store=True,
    )

    critical_exception_count = fields.Integer(
        compute="_compute_exception_counts",
        store=True,
    )

    _sql_constraints = [
        (
            "reinf_calculation_period_uniq",
            "unique (company_id, period)",
            "There is already a calculation of this competence for this company.",
        )
    ]

    @api.depends(
        "line_ids.base_amount",
        "line_ids.wh_amount",
        "line_ids.divergence_amount",
        "line_ids.state",
    )
    def _compute_totals(self):
        for record in self:
            lines = record.line_ids.filtered(lambda line: line.state != "excluded")
            record.line_count = len(lines)
            record.total_base_amount = sum(lines.mapped("base_amount"))
            record.total_wh_amount = sum(lines.mapped("wh_amount"))
            record.total_divergence_amount = sum(lines.mapped("divergence_amount"))

    @api.depends("exception_ids.critical", "exception_ids.ignored")
    def _compute_exception_counts(self):
        for record in self:
            record.exception_count = len(record.exception_ids)
            record.critical_exception_count = len(
                record.exception_ids.filtered("critical")
            )

    @api.constrains("period")
    def _check_period(self):
        for record in self:
            if not PERIOD_RE.match(record.period or "") or len(record.period) != 7:
                raise ValidationError(
                    _(
                        "The competence %(period)s is not valid: write it as "
                        "AAAA-MM.",
                        period=record.period,
                    )
                )

    def _period_range(self):
        """First and last day of the competence."""
        self.ensure_one()
        year, month = (int(part) for part in self.period.split("-"))
        return (
            date(year, month, 1),
            date(year, month, calendar.monthrange(year, month)[1]),
        )

    # ------------------------------------------------------------------
    # Collecting the data
    # ------------------------------------------------------------------

    def _nature_of_line(self, move_line):
        """The nature of income a line is declared under.

        The cascade is resolved by reading fields, and not by calling
        _reinf_nature_income() of the fiscal mixin, because account.move.line
        reaches the fiscal line by DELEGATION (_inherits), and delegation
        carries fields, never methods. The three fields below are all reachable
        from an account.move.line and from a fiscal document line alike.
        """
        return (
            move_line.reinf_nature_income_id
            or move_line.service_type_id.reinf_nature_income_id
            or move_line.partner_id.reinf_nature_income_id
        )

    def _withholdings_from_tax_lines(self, invoice):
        """Withholdings read from the posted tax lines of an invoice.

        This is the fallback of the fiscal fields, and it is the path that
        works in the general case: the *_wh_value fields belong to the fiscal
        tax engine, which re-derives them from fiscal_tax_ids on every write to
        the line, so a document that was not priced by the engine carries the
        withholding only in its tax lines.

        The amount of a tax line is distributed over the base lines that carry
        the tax, in proportion to their subtotal, because the nature of income
        is a property of the base line and one invoice can mix two natures.

        :return: {(move_line_id, tax): (base, withheld)}
        """
        result = {}
        for tax_line in invoice.line_ids.filtered("tax_line_id"):
            fiscal_group = tax_line.tax_line_id.tax_group_id.fiscal_tax_group_id
            if not fiscal_group or not fiscal_group.tax_withholding:
                continue
            tax = REINF_TAX_DOMAIN_MAP.get(fiscal_group.tax_domain)
            if not tax:
                continue
            withheld = abs(tax_line.balance)
            base_lines = invoice.invoice_line_ids.filtered(
                lambda line, tax_line=tax_line: tax_line.tax_line_id in line.tax_ids
            )
            total = sum(abs(line.price_subtotal) for line in base_lines)
            if not total:
                continue
            # tax_base_amount, not the subtotal: with a base reduction the
            # subtotal would declare a base the taxpayer never used. The split
            # between base lines stays proportional to the subtotal.
            taxed_base = abs(tax_line.tax_base_amount) or total
            for base_line in base_lines:
                share = abs(base_line.price_subtotal) / total
                key = (base_line.id, tax)
                previous = result.get(key, (0.0, 0.0))
                result[key] = (
                    previous[0] or taxed_base * share,
                    previous[1] + withheld * share,
                )
        return result

    def _withholdings_of_line(self, move_line, taxes, from_tax_lines=None):
        """Return [(tax, base, withheld)] of a move line, for the given taxes.

        The fiscal line comes first, because when the engine did price the
        document it is the richest source, and the tax lines answer for
        everything else.
        """
        result = []
        sign = -1 if move_line.move_id.move_type == "in_refund" else 1
        for tax in taxes:
            base = withheld = 0.0
            source = REINF_WITHHOLDING_SOURCES.get(tax)
            if source:
                # IRPF and RRA have no field of their own in the localization:
                # they are withholdings of a payment to an individual and enter
                # with the R-4010.
                withheld = move_line[source[0]] or 0.0
                base = move_line[source[1]] or 0.0
            if not withheld and from_tax_lines:
                base, withheld = from_tax_lines.get((move_line.id, tax), (0.0, 0.0))
            if not withheld:
                continue
            base = base or move_line.price_subtotal or 0.0
            result.append((tax, sign * base, sign * withheld))
        return result

    def _supplier_moves(self):
        """Posted supplier invoices whose credit falls in the competence."""
        self.ensure_one()
        date_from, date_to = self._period_range()
        return self.env["account.move"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("move_type", "in", SUPPLIER_MOVE_TYPES),
                ("state", "=", "posted"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
            ]
        )

    def _payment_allocations(self):
        """Return [(invoice, ratio, payment_date, payment)] settled here.

        The reconciliation is what says a supplier invoice was paid, and the
        share that was paid is what the PCC is due on: paying half of an
        invoice withholds half of the PCC.
        """
        self.ensure_one()
        date_from, date_to = self._period_range()
        partials = self.env["account.partial.reconcile"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("max_date", ">=", date_from),
                ("max_date", "<=", date_to),
            ]
        )
        allocations = []
        for partial in partials:
            invoice_line = partial.credit_move_id
            counterpart = partial.debit_move_id
            if invoice_line.move_id.move_type not in SUPPLIER_MOVE_TYPES:
                invoice_line, counterpart = counterpart, invoice_line
            invoice = invoice_line.move_id
            if invoice.move_type not in SUPPLIER_MOVE_TYPES:
                continue
            total = abs(invoice.amount_total)
            if not total:
                continue
            allocations.append(
                (
                    invoice,
                    min(partial.amount / total, 1.0),
                    partial.max_date,
                    counterpart.payment_id,
                )
            )
        return allocations

    # ------------------------------------------------------------------
    # Computing
    # ------------------------------------------------------------------

    def _prepare_line(self, invoice, move_line, tax, fg_date, base, withheld, payment):
        nature = self._nature_of_line(move_line)
        mapping = nature._tax_mapping(tax, fg_date) if nature else None
        return {
            "calculation_id": self.id,
            "partner_id": invoice.commercial_partner_id.id,
            "nature_income_id": nature.id,
            "revenue_code": mapping.revenue_code if mapping else False,
            "tax": tax,
            "fg_date": fg_date,
            "base_amount": base,
            "wh_amount": withheld,
            "source_move_id": invoice.id,
            "source_move_line_id": move_line.id,
            "source_payment_id": payment.id if payment else False,
        }

    def _prepare_exception(self, reason, **values):
        return dict({"calculation_id": self.id, "reason": reason}, **values)

    def _check_beneficiary(self, invoice, exceptions):
        """Return True when the beneficiary can be identified in an event."""
        partner = invoice.commercial_partner_id
        if not partner.cnpj_cpf:
            exceptions.append(
                self._prepare_exception(
                    "partner_without_cnpj",
                    partner_id=partner.id,
                    source_move_id=invoice.id,
                )
            )
            return False
        return True

    def _collect_credits(self, lines, exceptions):
        """Lines of the taxes whose taxable event is the credit."""
        self.ensure_one()
        for invoice in self._supplier_moves():
            beneficiary_ok = self._check_beneficiary(invoice, exceptions)
            from_tax_lines = self._withholdings_from_tax_lines(invoice)
            for move_line in invoice.invoice_line_ids:
                withholdings = self._withholdings_of_line(
                    move_line, REINF_TAXES_ON_CREDIT, from_tax_lines
                )
                if not withholdings:
                    continue
                nature = self._nature_of_line(move_line)
                if not nature:
                    exceptions.append(
                        self._prepare_exception(
                            "nature_missing",
                            partner_id=invoice.commercial_partner_id.id,
                            source_move_id=invoice.id,
                            source_move_line_id=move_line.id,
                            amount=sum(item[2] for item in withholdings),
                        )
                    )
                    continue
                if not beneficiary_ok:
                    continue
                for tax, base, withheld in withholdings:
                    lines.append(
                        self._prepare_line(
                            invoice,
                            move_line,
                            tax,
                            invoice.date,
                            base,
                            withheld,
                            None,
                        )
                    )

    def _collect_payments(self, lines, exceptions):
        """Lines of the taxes whose taxable event is the payment."""
        self.ensure_one()
        date_from, _date_to = self._period_range()
        pcc_taxes = tuple(
            tax for tax in REINF_WITHHOLDING_SOURCES if tax not in REINF_TAXES_ON_CREDIT
        )
        for invoice, ratio, payment_date, payment in self._payment_allocations():
            partner = invoice.commercial_partner_id
            if not self._check_beneficiary(invoice, exceptions):
                continue
            if partner.tax_framework == "1":
                # A beneficiary under the Simples Nacional suffers no PCC. The
                # income is still written, with the withholding in blank, which
                # is what the exception is for.
                exceptions.append(
                    self._prepare_exception(
                        "simples_beneficiary",
                        partner_id=partner.id,
                        source_move_id=invoice.id,
                    )
                )
                continue
            if ratio < 1.0:
                exceptions.append(
                    self._prepare_exception(
                        "partial_payment",
                        partner_id=partner.id,
                        source_move_id=invoice.id,
                        amount=invoice.amount_total * ratio,
                    )
                )
            if invoice.date < date_from:
                exceptions.append(
                    self._prepare_exception(
                        "prior_period_invoice",
                        partner_id=partner.id,
                        source_move_id=invoice.id,
                    )
                )
            from_tax_lines = self._withholdings_from_tax_lines(invoice)
            for move_line in invoice.invoice_line_ids:
                withholdings = self._withholdings_of_line(
                    move_line, pcc_taxes, from_tax_lines
                )
                if not withholdings:
                    continue
                nature = self._nature_of_line(move_line)
                if not nature:
                    exceptions.append(
                        self._prepare_exception(
                            "nature_missing",
                            partner_id=partner.id,
                            source_move_id=invoice.id,
                            source_move_line_id=move_line.id,
                        )
                    )
                    continue
                for tax, base, withheld in withholdings:
                    lines.append(
                        self._prepare_line(
                            invoice,
                            move_line,
                            tax,
                            payment_date,
                            base * ratio,
                            withheld * ratio,
                            payment,
                        )
                    )

    def _collapse_aggregate(self):
        """Turn the withholdings of PIS/PASEP, COFINS and CSLL into one value.

        The rule has two legs, and neither is a guess:

        1. **the nature admits the aggregate**, which is data: the column
           Tributo of the Tabela 01 says so, and it also says WHICH components
           the aggregate carries. It is not always the three: the cooperatives
           of work of the nature 15001 admit "IR, COFINS, PP, AGREGADO", with no
           CSLL, because the art. 32 I of the Law 10.833 does not require it.
           So an aggregate of 3,65% is legitimate, and refusing it would be the
           error. Reading the range of the code instead of this column breaks
           exactly there: 15048 and 15050 are also 15xxx and admit no aggregate;
        2. **the partiality has to be structural**. Missing a component that
           the nature does admit is not a dispensation of the nature: it comes
           from the beneficiary being exempt or at zero rate (IN RFB 459/2004,
           art. 2 par. 2, which asks for the legal ground of the exemption) or
           from a judicial measure (art. 10), and both demand their own revenue
           codes instead of the aggregate.

        The declared value is the SUM of what was actually withheld, never the
        rate applied to the base: the aggregate field of the layout carries the
        amount withheld, the tax authority does not recompute it, and the only
        rule over it is being greater than zero. The rate stays as a
        CONFERENCE: the expected value is compared to the sum, and the
        difference shows up on the line.

        The lines are replaced by one, and their composition goes to the note of
        the aggregated line: the conference screen has to show where the value
        came from without a second table.
        """
        self.ensure_one()
        tolerance = self.company_id.reinf_aggregate_tolerance or 0.0
        exceptions = []
        groups = defaultdict(lambda: self.env["l10n_br_reinf.calculation.line"])
        for line in self.line_ids:
            if line.tax not in REINF_AGGREGATABLE_TAXES or line.manually_verified:
                continue
            groups[(line.partner_id, line.nature_income_id, line.fg_date)] |= line

        for (partner, nature, fg_date), lines in groups.items():
            if not nature or not nature._admits_aggregate():
                continue
            mapping = nature._tax_mapping("aggregated", fg_date)
            if not mapping:
                continue
            components = nature._aggregate_components()
            withheld_taxes = set(lines.mapped("tax"))
            if partner.reinf_beneficiary_profile in ("exempt", "zero_rate", "judicial"):
                # The beneficiary, and not the nature, is why a component is
                # missing. That does not aggregate: it goes under the specific
                # revenue codes, and the judicial case still needs the process
                # declared in a R-1070.
                exceptions.append(
                    self._prepare_exception(
                        "judicial_suspension"
                        if partner.reinf_beneficiary_profile == "judicial"
                        else "aggregate_partial_not_structural",
                        partner_id=partner.id,
                        note=partner.reinf_exemption_legal_basis or "",
                    )
                )
                continue
            if withheld_taxes - components:
                # Withheld something the nature does not admit in the aggregate.
                # The accounting and the table disagree, and that is for a
                # person to look at, not for this method to average out.
                exceptions.append(
                    self._prepare_exception(
                        "aggregate_partial_not_structural",
                        partner_id=partner.id,
                        note=", ".join(sorted(withheld_taxes - components)),
                    )
                )
                continue
            if withheld_taxes != components:
                # A component the nature admits is missing: the partiality is
                # not structural, so the aggregate does not apply.
                exceptions.append(
                    self._prepare_exception(
                        "aggregate_partial_not_structural",
                        partner_id=partner.id,
                        note=", ".join(sorted(components - withheld_taxes)),
                    )
                )
                continue
            if (
                partner.reinf_beneficiary_profile == "work_cooperative"
                and "csll" in withheld_taxes
            ):
                # The art. 32 I does not require the CSLL of a cooperative of
                # work. It was withheld anyway, so somebody has to decide: the
                # line is NOT deleted here, because it is backed by accounting.
                exceptions.append(
                    self._prepare_exception(
                        "cooperative_csll_withheld",
                        partner_id=partner.id,
                        amount=sum(
                            lines.filtered(lambda line: line.tax == "csll").mapped(
                                "wh_amount"
                            )
                        ),
                    )
                )
            base = max(lines.mapped("base_amount"))
            aggregated = round(sum(line.wh_amount for line in lines), 2)
            divergence = 0.0
            revenue_code = self.env["l10n_br_reinf.revenue.code"]._valid_at(
                mapping.revenue_code, fg_date
            )
            if revenue_code and revenue_code.rate:
                # The rate is a conference, not the value: it only makes sense
                # when the aggregate carries the full set of components, since
                # the expected rate of a partial aggregate is not published as
                # a rate of its own.
                if components == set(REINF_AGGREGATABLE_TAXES):
                    expected = round(base * revenue_code.rate / 100.0, 2)
                    divergence = round(expected - aggregated, 2)
            else:
                exceptions.append(
                    self._prepare_exception(
                        "aggregate_rate_missing",
                        partner_id=partner.id,
                        note=mapping.revenue_code,
                    )
                )
            composition = ", ".join(
                f"{dict(REINF_WITHHOLDING_TAXES)[line.tax]} "
                f"{line.wh_amount:.2f}".replace(".", ",")
                for line in lines.sorted("tax")
            )
            self.env["l10n_br_reinf.calculation.line"].create(
                {
                    "calculation_id": self.id,
                    "partner_id": partner.id,
                    "nature_income_id": nature.id,
                    "revenue_code": mapping.revenue_code,
                    "tax": "aggregated",
                    "fg_date": fg_date,
                    "base_amount": base,
                    "wh_amount": aggregated,
                    "divergence_amount": divergence,
                    "state": "divergent" if abs(divergence) > tolerance else "ok",
                    "source_move_id": lines[0].source_move_id.id,
                    "source_move_line_id": lines[0].source_move_line_id.id,
                    "source_payment_id": lines[0].source_payment_id.id,
                    "note": composition,
                }
            )
            lines.unlink()
            if abs(divergence) > tolerance:
                exceptions.append(
                    self._prepare_exception(
                        "aggregate_divergence",
                        partner_id=partner.id,
                        amount=divergence,
                        note=composition,
                    )
                )
        if exceptions:
            self.env["l10n_br_reinf.calculation.exception"].create(exceptions)
        return True

    def action_compute(self):
        """Rebuild the lines of the competence out of the accounting.

        Recomputing is safe on purpose: the lines somebody verified by hand are
        kept, everything else is rebuilt, and the chatter records what came out
        so a second run is auditable instead of mysterious.
        """
        for record in self:
            if record.state in ("closed", "transmitted"):
                raise UserError(
                    _(
                        "The competence %s is closed. Reopen it before " "recomputing.",
                        record.period,
                    )
                )
            kept = record.line_ids.filtered("manually_verified")
            (record.line_ids - kept).unlink()
            record.exception_ids.filtered(lambda item: not item.ignored).unlink()

            lines, exceptions = [], []
            record._collect_credits(lines, exceptions)
            record._collect_payments(lines, exceptions)
            self.env["l10n_br_reinf.calculation.line"].create(lines)
            self.env["l10n_br_reinf.calculation.exception"].create(exceptions)
            record._collapse_aggregate()
            record.action_generate_darfs()
            record.state = "computed"
            record.message_post(
                body=_(
                    "Computed: %(lines)s lines, %(kept)s kept from a manual "
                    "check, %(exceptions)s exceptions (%(critical)s critical).",
                    lines=len(lines),
                    kept=len(kept),
                    exceptions=len(exceptions),
                    critical=record.critical_exception_count,
                )
            )
        return True

    def _previous_period(self):
        """The competence right before this one, as AAAA-MM."""
        self.ensure_one()
        year, month = (int(part) for part in self.period.split("-"))
        month -= 1
        if month < 1:
            month, year = 12, year - 1
        return f"{year:04d}-{month:02d}"

    def _carried_darf(self, revenue_code):
        """The DARF of the previous competence whose balance travels here."""
        self.ensure_one()
        return self.env["l10n_br_reinf.darf"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("period", "=", self._previous_period()),
                ("revenue_code", "=", revenue_code),
                ("state", "=", "carried"),
            ],
            limit=1,
        )

    def action_generate_darfs(self):
        """Group the withholdings of the competence by revenue code.

        The mirror is rebuilt from the lines every time, except for what was
        already confirmed or reconciled, which is history and does not move.
        """
        darf_model = self.env["l10n_br_reinf.darf"]
        for record in self:
            record.darf_ids.filtered(
                lambda darf: darf.state in ("draft", "carried")
            ).unlink()
            groups = defaultdict(lambda: self.env["l10n_br_reinf.calculation.line"])
            for line in record.line_ids:
                if line.state == "excluded" or not line.revenue_code:
                    continue
                if not line.wh_amount:
                    continue
                groups[line.revenue_code] |= line

            exceptions = []
            for revenue_code, lines in groups.items():
                carried = record._carried_darf(revenue_code)
                darf = darf_model.create(
                    {
                        "calculation_id": record.id,
                        "revenue_code": revenue_code,
                        "amount": round(sum(lines.mapped("wh_amount")), 2),
                        "carried_amount": carried.total_amount if carried else 0.0,
                        "carried_from_id": carried.id if carried else False,
                        "due_date": darf_model._due_date_of(
                            record.period, record.company_id
                        ),
                    }
                )
                lines.write({"darf_id": darf.id})
                if darf._is_below_minimum():
                    # Not collected in this competence: the balance travels to
                    # the next one under the same revenue code, and the income
                    # is still declared, with the withholding in blank.
                    darf.state = "carried"
                    exceptions.append(
                        record._prepare_exception(
                            "below_minimum",
                            amount=darf.total_amount,
                            note=revenue_code,
                        )
                    )
            if exceptions:
                self.env["l10n_br_reinf.calculation.exception"].create(exceptions)
        return True

    def action_verify(self):
        """Mark the competence as checked by a person."""
        for record in self:
            if record.state != "computed":
                raise UserError(_("Only a computed competence can be verified."))
            record.state = "verified"
        return True

    def action_close(self):
        """Close the competence and generate its events.

        A critical exception blocks it, and that is the point of the list: the
        competence does not close over a beneficiary with no CNPJ or a payment
        with no nature of income, because those become a rejected event.
        Closing generates the R-4020; it never transmits.
        """
        for record in self:
            if record.state not in ("computed", "verified"):
                raise UserError(
                    _("Only a computed or verified competence can be closed.")
                )
            if record.critical_exception_count:
                raise UserError(
                    _(
                        "The competence %(period)s has %(count)s critical "
                        "exceptions. Solve them, or ignore them with a reason, "
                        "before closing.",
                        period=record.period,
                        count=record.critical_exception_count,
                    )
                )
            events = record._generate_r4020()
            record.state = "closed"
            record.message_post(
                body=_(
                    "Competence closed: %(events)s R-4020 events generated.",
                    events=len(events),
                )
            )
        return True

    def action_set_draft(self):
        for record in self:
            if record.state in ("closed", "transmitted"):
                raise UserError(_("A closed competence does not go back to draft."))
            record.state = "draft"
        return True
