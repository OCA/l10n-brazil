# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestTaxAssessment(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.Assessment = cls.env["l10n_br_tax.assessment"]

        cls.account_payable = cls.env["account.account"].create(
            {
                "name": "ICMS a recolher",
                "code": "TSTPAY",
                "account_type": "liability_current",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.account_receivable = cls.env["account.account"].create(
            {
                "name": "ICMS a recuperar",
                "code": "TSTREC",
                "account_type": "asset_current",
                "company_id": cls.company_data["company"].id,
            }
        )

    def setUp(self):
        super().setUp()
        # One group per test: `property_tax_payable_account_id` is
        # company_dependent (ir.property) and its cache does not follow the
        # rollback, so a class-level group would let the test that configures
        # the accounts leak into the one that expects them empty.
        self.group = self.env["account.tax.group"].create({"name": "ICMS (teste)"})

    def _configure_group(self):
        self.group.with_company(self.company_data["company"]).write(
            {
                "property_tax_payable_account_id": self.account_payable.id,
                "property_tax_receivable_account_id": self.account_receivable.id,
            }
        )

    def _new_assessment(self, date_from="2026-07-01", date_to="2026-07-31", group=None):
        return self.Assessment.create(
            {
                "company_id": self.company_data["company"].id,
                "tax_group_id": (group or self.group).id,
                "date_from": date_from,
                "date_to": date_to,
            }
        )

    def _regime_group(self, regime):
        """One tax group per regime: the partition criterion of decision D1."""
        return self.env["account.tax.group"].create(
            {"name": "PIS %s (teste)" % regime, "regime": regime}
        )

    def _add_line(self, assessment, kind, tax_amount, source="manual", code=None):
        vals = {
            "assessment_id": assessment.id,
            "kind": kind,
            "tax_amount": tax_amount,
            "source": source,
            "description": "ajuste de teste",
        }
        if code:
            vals["adjustment_code"] = code
        return self.env["l10n_br_tax.assessment.line"].create(vals)

    # ------------------------------------------------------------------
    # running account
    # ------------------------------------------------------------------

    def test_balance_is_debit_minus_credit(self):
        """The period balance is debits minus credits."""
        a = self._new_assessment()
        self._add_line(a, "debit", 1000.0)
        self._add_line(a, "credit", 300.0)
        self.assertEqual(a.balance, 700.0)
        self.assertEqual(a.amount_payable, 700.0)
        self.assertEqual(a.amount_carried_forward, 0.0)

    def test_credit_balance_is_carried_forward_not_payable(self):
        """More credit than debit does not become negative tax payable.

        It becomes a credit balance to carry over. Mixing the two up is the
        mistake that prints a payment slip with a negative amount.
        """
        a = self._new_assessment()
        self._add_line(a, "debit", 200.0)
        self._add_line(a, "credit", 500.0)
        self.assertEqual(a.balance, -300.0)
        self.assertEqual(a.amount_payable, 0.0)
        self.assertEqual(a.amount_carried_forward, 300.0)

    def test_previous_credit_balance_is_deducted(self):
        """The previous period credit balance feeds the next assessment."""
        jun = self._new_assessment("2026-06-01", "2026-06-30")
        self._add_line(jun, "credit", 400.0)
        jun.state = "computed"
        self.assertEqual(jun.amount_carried_forward, 400.0)

        jul = self._new_assessment()
        jul.action_compute()
        self.assertEqual(jul.previous_assessment_id, jun)
        self.assertEqual(jul.previous_balance, 400.0)

        self._add_line(jul, "debit", 1000.0)
        # 1000 of debit minus 400 carried over
        self.assertEqual(jul.balance, 600.0)
        self.assertEqual(jul.amount_payable, 600.0)

    # ------------------------------------------------------------------
    # table 5.1.1 adjustments, which is what E110 and E111 require
    # ------------------------------------------------------------------

    def test_adjustment_code_classifies_the_line(self):
        """The fourth COD_AJ_APUR digit decides the E110 field.

        SP00 0001 is other debits and SP01 0001 is a credit reversal: both add
        to the debit side, but the tax authority wants them in different fields.
        """
        a = self._new_assessment()
        self._add_line(a, "debit", 100.0, code="SP000001")
        self._add_line(a, "credit_reversal", 40.0, code="SP010001")
        self._add_line(a, "credit", 30.0, code="SP020001")
        self._add_line(a, "debit_reversal", 25.0, code="SP030001")

        self.assertEqual(a.adjustment_debit_total, 100.0)
        self.assertEqual(a.credit_reversal_total, 40.0)
        self.assertEqual(a.adjustment_credit_total, 30.0)
        self.assertEqual(a.debit_reversal_total, 25.0)
        # assessed and adjustment do not mix: fields 02 and 06 stay at zero
        self.assertEqual(a.debit_total, 0.0)
        self.assertEqual(a.credit_total, 0.0)
        # the offsetting uses all four: 140 of debit against 55 of credit
        self.assertEqual(a.balance, 85.0)

    def test_deduction_reduces_payable_but_not_the_balance(self):
        """A deduction offsets what was assessed, it is not part of the offsetting.

        Adding a deduction as a credit would produce a credit balance to carry
        over where there is in fact no credit at all.
        """
        a = self._new_assessment()
        self._add_line(a, "debit", 1000.0)
        self._add_line(a, "deduction", 300.0, code="SP040001")
        self.assertEqual(a.balance, 1000.0)
        self.assertEqual(a.assessed_balance, 1000.0)
        self.assertEqual(a.deduction_total, 300.0)
        self.assertEqual(a.amount_payable, 700.0)
        self.assertEqual(a.amount_carried_forward, 0.0)

    def test_deduction_never_makes_payable_negative(self):
        """A deduction larger than the amount due never goes negative."""
        a = self._new_assessment()
        self._add_line(a, "debit", 100.0)
        self._add_line(a, "deduction", 250.0, code="SP040001")
        self.assertEqual(a.amount_payable, 0.0)
        self.assertEqual(a.amount_carried_forward, 0.0)

    def test_special_debit_does_not_touch_the_balance(self):
        """A special debit is outside the assessment: it reports, not assesses."""
        a = self._new_assessment()
        self._add_line(a, "debit", 500.0)
        self._add_line(a, "special_debit", 80.0, code="SP050001")
        self.assertEqual(a.special_debit_total, 80.0)
        self.assertEqual(a.balance, 500.0)
        self.assertEqual(a.amount_payable, 500.0)

    def test_adjustment_code_inconsistent_with_kind_is_refused(self):
        """A credit reversal booked as a credit would flip the tax."""
        a = self._new_assessment()
        with self.assertRaises(ValidationError):
            self._add_line(a, "credit", 40.0, code="SP010001")

    def test_malformed_adjustment_code_is_refused(self):
        a = self._new_assessment()
        with self.assertRaises(ValidationError):
            self._add_line(a, "debit", 10.0, code="SP1")
        with self.assertRaises(ValidationError):
            # 9 is not an adjustment kind in table 5.1.1
            self._add_line(a, "debit", 10.0, code="SP090001")
        with self.assertRaises(ValidationError):
            # the third digit tells the assessment: only 0 (own) or 1 (ST)
            self._add_line(a, "debit", 10.0, code="SP900001")

    def test_ipi_adjustment_code_is_3_positions(self):
        """IPI adjustments come from table 4.5.4, not from the ICMS 5.1.1.

        The 8-position shape (state, assessment, kind, sequence) only exists
        in the ICMS table; forcing it on an IPI assessment would make every
        legitimate E530 adjustment impossible to book.
        """
        group = self.env["account.tax.group"].create(
            {
                "name": "IPI (teste)",
                "fiscal_tax_group_id": self.env.ref("l10n_br_fiscal.tax_group_ipi").id,
            }
        )
        a = self._new_assessment(group=group)
        line = self._add_line(a, "debit", 10.0, code="199")
        # the fourth digit means nothing outside table 5.1.1
        self.assertFalse(line.adjustment_kind)
        with self.assertRaises(ValidationError):
            self._add_line(a, "debit", 10.0, code="SP000001")

    def test_manual_line_requires_description(self):
        """An adjustment with no reason has nothing to write into E111."""
        a = self._new_assessment()
        with self.assertRaises(ValidationError):
            self.env["l10n_br_tax.assessment.line"].create(
                {
                    "assessment_id": a.id,
                    "kind": "debit",
                    "tax_amount": 10.0,
                    "source": "manual",
                }
            )

    def test_withholding_reduces_payable_in_its_own_field(self):
        """Withholding offsets the amount due without being a deduction.

        EFD Contribuicoes record M200 asks for both in separate fields, and
        folding one into the other would make the record impossible to rebuild.
        """
        a = self._new_assessment()
        self._add_line(a, "debit", 1000.0)
        self._add_line(a, "deduction", 100.0, code="SP040001")
        self._add_line(a, "withholding", 250.0)
        self.assertEqual(a.deduction_total, 100.0)
        self.assertEqual(a.withholding_total, 250.0)
        self.assertEqual(a.balance, 1000.0)
        self.assertEqual(a.amount_payable, 650.0)

    def test_same_period_two_regimes_coexist(self):
        """Cumulative and non-cumulative PIS are distinct assessments.

        The regime lives on the tax group (one group per regime), so a mixed
        taxpayer gets two groups and two assessments, and neither can ever
        read the other's taxes: the setup that doubled the M200 is not
        representable.
        """
        nc = self._new_assessment(group=self._regime_group("non_cumulative"))
        cum = self._new_assessment(group=self._regime_group("cumulative"))
        self.assertNotEqual(nc, cum)
        self.assertEqual(nc.regime, "non_cumulative")
        self.assertEqual(cum.regime, "cumulative")
        # the partition is by group, so the computed lines can never overlap
        self.assertFalse(set(nc._get_taxes().ids) & set(cum._get_taxes().ids))
        self._add_line(nc, "debit", 300.0)
        self._add_line(cum, "debit", 120.0)
        self.assertEqual(nc.amount_payable, 300.0)
        self.assertEqual(cum.amount_payable, 120.0)

    def test_previous_balance_does_not_cross_regimes(self):
        """A cumulative credit balance does not offset the non-cumulative one."""
        cum_group = self._regime_group("cumulative")
        jun = self._new_assessment("2026-06-01", "2026-06-30", group=cum_group)
        self._add_line(jun, "credit", 500.0)
        jun.state = "computed"

        jul = self._new_assessment(group=self._regime_group("non_cumulative"))
        jul.action_compute()
        self.assertFalse(jul.previous_assessment_id)
        self.assertEqual(jul.previous_balance, 0.0)

    # ------------------------------------------------------------------
    # buckets that only exist in some layouts (F4)
    # ------------------------------------------------------------------

    def _domain_group(self, fiscal_ref, name):
        return self.env["account.tax.group"].create(
            {
                "name": name,
                "fiscal_tax_group_id": self.env.ref(fiscal_ref).id,
            }
        )

    def test_withholding_is_refused_in_an_icms_assessment(self):
        """The E110 has no withholding field.

        A withholding line in an ICMS assessment breaks the equality
        field 13 = field 11 - field 12, which the PVA validates.
        """
        group = self._domain_group("l10n_br_fiscal.tax_group_icms", "ICMS dom")
        a = self._new_assessment(group=group)
        with self.assertRaises(ValidationError):
            self._add_line(a, "withholding", 50.0)

    def test_special_debit_is_refused_in_a_pis_assessment(self):
        """The M200 has no special debit field: the amount would vanish."""
        group = self._domain_group("l10n_br_fiscal.tax_group_pis", "PIS dom")
        a = self._new_assessment(group=group)
        with self.assertRaises(ValidationError):
            self._add_line(a, "special_debit", 50.0, code="SP050001")

    def test_unknown_domain_blocks_nothing(self):
        """Without a fiscal group there is no layout to contradict yet."""
        a = self._new_assessment()
        self._add_line(a, "withholding", 50.0)
        self._add_line(a, "special_debit", 20.0, code="SP050001")
        self.assertEqual(a.withholding_total, 50.0)

    # ------------------------------------------------------------------
    # stale carried balance (F6)
    # ------------------------------------------------------------------

    def test_posting_on_a_stale_previous_balance_is_refused(self):
        """Closing must not chain a carried balance the previous period no
        longer transports: reassess first, then close."""
        self._configure_group()
        jun = self._new_assessment("2026-06-01", "2026-06-30")
        self._add_line(jun, "credit", 400.0, source="computed")
        jun.state = "computed"

        jul = self._new_assessment()
        jul.action_compute()
        self.assertEqual(jul.previous_balance, 400.0)

        # june changes AFTER july was assessed
        self._add_line(jun, "credit", 100.0, source="computed")
        self.assertEqual(jun.amount_carried_forward, 500.0)

        with self.assertRaises(UserError):
            jul.action_post()

        # reassessing refreshes the snapshot and unlocks the closing
        jul.action_compute()
        self.assertEqual(jul.previous_balance, 500.0)
        jul.action_post()
        self.assertEqual(jul.state, "posted")

    # ------------------------------------------------------------------
    # validation
    # ------------------------------------------------------------------

    def test_post_without_configured_accounts_raises(self):
        """Without the tax group accounts there is no closing.

        The chart of accounts installs GLOBAL `ir.property` records
        (res_id=False) for `property_tax_payable_account_id` and its sibling, so
        every new group is born with an account. To exercise the check the
        company property has to be cleared explicitly, which is the real
        scenario the guard protects: a database with no chart of accounts, or a
        company whose property was removed.
        """
        self.group.with_company(self.company_data["company"]).write(
            {
                "property_tax_payable_account_id": False,
                "property_tax_receivable_account_id": False,
            }
        )
        a = self._new_assessment()
        a.action_compute()
        with self.assertRaises(UserError) as ctx:
            a.action_post()
        self.assertIn("grupo de imposto", str(ctx.exception))

    def test_post_requires_computed_state(self):
        a = self._new_assessment()
        with self.assertRaises(UserError):
            a.action_post()

    # ------------------------------------------------------------------
    # closing
    # ------------------------------------------------------------------

    def test_closing_move_consumes_the_smaller_side(self):
        """The entry moves the CONSUMED side, never the net balance.

        Sales credited 1000 into payable and purchases debited 250 into
        recoverable. Closing consumes the 250: payable is left with the 750
        of the payment slip and recoverable is left at zero. Moving the net
        750, as a first version did, left recoverable with a NEGATIVE asset
        of 500 and payable with 250, and a test that only checked that the
        entry balances protected the defect.
        """
        self._configure_group()
        a = self._new_assessment()
        a.action_compute()
        self._add_line(a, "debit", 1000.0, source="computed")
        self._add_line(a, "credit", 250.0, source="computed")
        a.action_post()

        self.assertEqual(a.state, "posted")
        move = a.move_id
        self.assertTrue(move)
        linha_pagar = move.line_ids.filtered(
            lambda line: line.account_id == self.account_payable
        )
        linha_recuperar = move.line_ids.filtered(
            lambda line: line.account_id == self.account_receivable
        )
        # consumes the credit side (250), leaving 750 due in payable
        self.assertAlmostEqual(linha_pagar.debit, 250.0, places=2)
        self.assertAlmostEqual(linha_recuperar.credit, 250.0, places=2)
        # resulting balances of the pair: payable keeps the slip, recoverable
        # zeroes out (1000 credit - 250 debit consumed = 750 credit due)
        self.assertAlmostEqual(1000.0 - linha_pagar.debit, a.amount_payable, places=2)

    def test_closing_without_credit_creates_no_move(self):
        """Only debits: nothing to consume, the accounts are already right.

        The payable account already holds the full amount due from the
        invoices; an entry here would only move value to the wrong place.
        """
        self._configure_group()
        a = self._new_assessment()
        a.action_compute()
        self._add_line(a, "debit", 1000.0, source="computed")
        a.action_post()
        self.assertEqual(a.state, "posted")
        self.assertFalse(a.move_id)
        self.assertEqual(a.amount_payable, 1000.0)

    def test_closing_with_credit_balance_consumes_the_debit_side(self):
        """More credit than debit: consume the debit, the rest carries over."""
        self._configure_group()
        a = self._new_assessment()
        a.action_compute()
        self._add_line(a, "debit", 200.0, source="computed")
        self._add_line(a, "credit", 500.0, source="computed")
        a.action_post()
        move = a.move_id
        self.assertTrue(move)
        linha_pagar = move.line_ids.filtered(
            lambda line: line.account_id == self.account_payable
        )
        self.assertAlmostEqual(linha_pagar.debit, 200.0, places=2)
        self.assertAlmostEqual(a.amount_carried_forward, 300.0, places=2)

    def test_period_without_movement_closes_without_move(self):
        """A period with no movement closes without an entry, but it closes.

        That is what keeps the credit balance chain without a gap: skipping the
        period would make the next assessment look for the previous one and
        find nothing.
        """
        self._configure_group()
        a = self._new_assessment()
        a.action_compute()
        a.action_post()
        self.assertEqual(a.state, "posted")
        self.assertFalse(a.move_id)

    def test_recompute_keeps_manual_adjustments(self):
        """Reassessing rebuilds the move line side and keeps the manual adjustment.

        That is what allows fixing the assessment without losing the E111 that
        was typed in.
        """
        a = self._new_assessment()
        a.action_compute()
        self._add_line(a, "debit", 90.0, source="manual")
        a.action_compute()
        manuais = a.line_ids.filtered(lambda line: line.source == "manual")
        self.assertEqual(len(manuais), 1)
        self.assertAlmostEqual(manuais.tax_amount, 90.0, places=2)

    @mute_logger("odoo.sql_db")
    def test_same_period_and_group_cannot_be_duplicated(self):
        """Two assessments of the same group, regime and period would double the tax.

        The regime is part of the key with a required value precisely so this
        keeps holding: with a null regime Postgres would let the duplicate
        through, because NULL is never equal to NULL.
        """
        self._new_assessment()
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._new_assessment()

    def test_draft_again_removes_the_closing_move(self):
        self._configure_group()
        a = self._new_assessment()
        a.action_compute()
        self._add_line(a, "debit", 500.0, source="computed")
        self._add_line(a, "credit", 120.0, source="computed")
        a.action_post()
        self.assertTrue(a.move_id)
        a.action_draft()
        self.assertEqual(a.state, "draft")
        self.assertFalse(a.move_id)

    def test_closing_never_consumes_more_than_the_account_holds(self):
        """A manual adjustment must not drive an account negative.

        An adjustment carries no journal item of its own: it is a number the
        tax authority wants declared, not a movement in the books. It still
        takes part in the offsetting, so it can make one side of the assessment
        larger than the balance its account actually holds. Consuming that side
        credits the recoverable account by more than was ever debited into it,
        and the asset goes negative, which is the same defect a purchase return
        used to cause.

        Sale 100 into payable, purchase 10 into recoverable, and a manual
        credit adjustment of 500 that exists only in the assessment. Whatever
        the closing entry moves, it cannot exceed the 10 the recoverable
        account holds.
        """
        self._configure_group()
        assessment = self._new_assessment()
        assessment.action_compute()
        self._add_line(assessment, "debit", 100.0, source="computed")
        self._add_line(assessment, "credit", 10.0, source="computed")
        self._add_line(assessment, "credit", 500.0, code="SP020001")

        booked_credit_side = 10.0
        self.assertLessEqual(
            assessment._closing_offset(),
            booked_credit_side,
            "the closing consumes more than the recoverable account holds, "
            "which leaves it a negative asset",
        )


@tagged("post_install", "-at_install")
class TestTaxAssessmentCompute(AccountTestInvoicingCommon):
    """`action_compute` against REAL invoices, refunds included.

    The council found that the whole suite exercised the compute only against
    empty tax groups: the bridge to the accounting, which is the module's
    reason to exist, had zero coverage. These tests are that bridge.
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.group = cls.env["account.tax.group"].create({"name": "ICMS (compute)"})
        cls.sale_tax = cls.env["account.tax"].create(
            {
                "name": "ICMS 18% saida (teste)",
                "amount": 18.0,
                "type_tax_use": "sale",
                "tax_group_id": cls.group.id,
                "company_id": cls.company.id,
            }
        )
        cls.purchase_tax = cls.env["account.tax"].create(
            {
                "name": "ICMS 18% entrada (teste)",
                "amount": 18.0,
                "type_tax_use": "purchase",
                "tax_group_id": cls.group.id,
                "company_id": cls.company.id,
            }
        )

    def _assessment(self):
        return self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": self.group.id,
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
            }
        )

    def test_compute_reads_posted_invoices(self):
        """The assessed line carries the tax of the posted invoices."""
        self.init_invoice(
            "out_invoice",
            invoice_date="2026-07-10",
            amounts=[1000.0],
            taxes=self.sale_tax,
            post=True,
        )
        a = self._assessment()
        a.action_compute()
        debit = a.line_ids.filtered(lambda line: line.kind == "debit")
        self.assertEqual(len(debit), 1)
        self.assertAlmostEqual(debit.tax_amount, 180.0, places=2)
        self.assertAlmostEqual(debit.base_amount, 1000.0, places=2)
        self.assertAlmostEqual(a.debit_total, 180.0, places=2)
        self.assertAlmostEqual(a.amount_payable, 180.0, places=2)

    def test_unclassifiable_tax_is_logged_not_dropped(self):
        """A tax outside sale/purchase leaves a trail in the chatter.

        Vanishing in silence was the defect: a misconfigured withholding tax
        simply disappeared from the assessment with nothing to flag it.
        """
        self.env["account.tax"].create(
            {
                "name": "Retencao mal configurada (teste)",
                "amount": 1.0,
                "type_tax_use": "none",
                "tax_group_id": self.group.id,
                "company_id": self.company.id,
            }
        )
        a = self._assessment()
        a.action_compute()
        bodies = " ".join(a.message_ids.mapped("body"))
        self.assertIn("Retencao mal configurada (teste)", bodies)

    def test_sale_refund_becomes_a_debit_reversal(self):
        """A sale refund is E110 field 09, never netted into field 02.

        Netting closes on the right total with the wrong breakdown, which is
        exactly the defect the council named F3: the file looks right until a
        period has a return, which is routine, not exotic.
        """
        self.init_invoice(
            "out_invoice",
            invoice_date="2026-07-10",
            amounts=[1000.0],
            taxes=self.sale_tax,
            post=True,
        )
        self.init_invoice(
            "out_refund",
            invoice_date="2026-07-20",
            amounts=[200.0],
            taxes=self.sale_tax,
            post=True,
        )
        a = self._assessment()
        a.action_compute()
        # gross stays gross, the reversal gets its own bucket
        self.assertAlmostEqual(a.debit_total, 180.0, places=2)
        self.assertAlmostEqual(a.debit_reversal_total, 36.0, places=2)
        # and the offsetting still closes on the net
        self.assertAlmostEqual(a.balance, 144.0, places=2)
        reversal = a.line_ids.filtered(lambda line: line.kind == "debit_reversal")
        self.assertEqual(reversal.source, "computed")
        self.assertAlmostEqual(reversal.base_amount, 200.0, places=2)

    def test_purchase_refund_becomes_a_credit_reversal(self):
        """A purchase refund is E110 field 05, apart from the gross credit."""
        self.init_invoice(
            "in_invoice",
            invoice_date="2026-07-05",
            amounts=[500.0],
            taxes=self.purchase_tax,
            post=True,
        )
        self.init_invoice(
            "in_refund",
            invoice_date="2026-07-25",
            amounts=[100.0],
            taxes=self.purchase_tax,
            post=True,
        )
        a = self._assessment()
        a.action_compute()
        self.assertAlmostEqual(a.credit_total, 90.0, places=2)
        self.assertAlmostEqual(a.credit_reversal_total, 18.0, places=2)
        # credit side 90, debit side 18 (the reversal adds to the debit side)
        self.assertAlmostEqual(a.balance, -72.0, places=2)
        self.assertAlmostEqual(a.amount_carried_forward, 72.0, places=2)

    def test_recompute_rebuilds_the_reversals(self):
        """Reassessing does not duplicate computed reversals."""
        self.init_invoice(
            "out_invoice",
            invoice_date="2026-07-10",
            amounts=[1000.0],
            taxes=self.sale_tax,
            post=True,
        )
        self.init_invoice(
            "out_refund",
            invoice_date="2026-07-20",
            amounts=[200.0],
            taxes=self.sale_tax,
            post=True,
        )
        a = self._assessment()
        a.action_compute()
        a.action_compute()
        self.assertEqual(
            len(a.line_ids.filtered(lambda line: line.kind == "debit_reversal")), 1
        )


@tagged("post_install", "-at_install")
class TestTaxAssessmentDemo(AccountTestInvoicingCommon):
    """The demo data has to actually assess, not merely exist.

    The period is computed at install time, so a demo record that was only
    created would pass this test while showing an assessment for the wrong
    month.
    """

    def test_demo_assessment_is_computed_for_the_current_month(self):
        assessment = self.env.ref(
            "l10n_br_tax_assessment.demo_assessment_icms", raise_if_not_found=False
        )
        if not assessment:
            self.skipTest("database without demo data")
        # The demo data lives in the localization's Brazilian company, not in
        # the test user's, and the multi-company `ir.rule` blocks the read.
        # Reading as sudo keeps this test about the DATA rather than turning it
        # into a multi-company test.
        assessment = assessment.sudo()
        today = fields.Date.context_today(assessment)
        # computed at install time; posted is even stronger (a user or a
        # validation run may have closed it since)
        self.assertIn(assessment.state, ("computed", "posted"))
        self.assertEqual(assessment.tax_domain, "icms")
        self.assertEqual(assessment.date_from, today.replace(day=1))
        self.assertEqual(assessment.date_to.month, today.month)
        self.assertEqual(assessment.date_to.year, today.year)
        # the group has to be the one the company taxes use, otherwise the
        # assessment reads from a group no journal item ever references
        self.assertTrue(assessment._get_taxes())

    def test_demo_adjustment_is_classified_by_its_code(self):
        line = self.env.ref(
            "l10n_br_tax_assessment.demo_assessment_icms_adjustment",
            raise_if_not_found=False,
        )
        if not line:
            self.skipTest("database without demo data")
        line = line.sudo()
        self.assertEqual(line.adjustment_kind, "other_debit")
        self.assertEqual(line.kind, "debit")


@tagged("post_install", "-at_install")
class TestTaxAssessmentClosingBook(AccountTestInvoicingCommon):
    """Closing against the ACCOUNTS the invoices actually posted to.

    Every other closing test builds the running account with synthetic lines
    and checks the arithmetic of the entry. None of them post real invoices
    and read the resulting BOOK balance, so the bridge between the escrituracao
    and the closing entry had no coverage: the point where the sign convention
    of a return could diverge from how it was booked.

    Here the taxes post to the same payable/receivable accounts the group
    closes into, so after posting the closing entry the accounts must show the
    payment slip on one side and zero (never a negative asset) on the other.
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.payable = cls.env["account.account"].create(
            {
                "name": "ICMS a recolher",
                "code": "TAXPAY",
                "account_type": "liability_current",
                "company_id": cls.company.id,
            }
        )
        cls.receivable = cls.env["account.account"].create(
            {
                "name": "ICMS a recuperar",
                "code": "TAXREC",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.group = cls.env["account.tax.group"].create({"name": "ICMS (encerramento)"})
        cls.group.with_company(cls.company).write(
            {
                "property_tax_payable_account_id": cls.payable.id,
                "property_tax_receivable_account_id": cls.receivable.id,
            }
        )
        # A sale tax books its amount into the payable account (the invoices
        # credit it) and a purchase tax into the recoverable one (they debit
        # it). Pinning the repartition account is what makes the invoices land
        # on the very accounts the closing entry then consumes.
        cls.sale_tax = cls._tax("ICMS 18% saida", "sale", cls.payable)
        cls.purchase_tax = cls._tax("ICMS 18% entrada", "purchase", cls.receivable)

    @classmethod
    def _tax(cls, name, type_tax_use, account):
        return cls.env["account.tax"].create(
            {
                "name": "%s (teste)" % name,
                "amount": 18.0,
                "type_tax_use": type_tax_use,
                "tax_group_id": cls.group.id,
                "company_id": cls.company.id,
                "invoice_repartition_line_ids": [
                    (0, 0, {"repartition_type": "base", "factor_percent": 100.0}),
                    (
                        0,
                        0,
                        {
                            "repartition_type": "tax",
                            "factor_percent": 100.0,
                            "account_id": account.id,
                        },
                    ),
                ],
                "refund_repartition_line_ids": [
                    (0, 0, {"repartition_type": "base", "factor_percent": 100.0}),
                    (
                        0,
                        0,
                        {
                            "repartition_type": "tax",
                            "factor_percent": 100.0,
                            "account_id": account.id,
                        },
                    ),
                ],
            }
        )

    def _book_balance(self, account):
        """Signed balance of the account over the posted entries (debit - credit)."""
        self.env["account.move.line"].flush_model()
        lines = self.env["account.move.line"].search(
            [
                ("account_id", "=", account.id),
                ("parent_state", "=", "posted"),
                ("company_id", "=", self.company.id),
            ]
        )
        return sum(lines.mapped("balance"))

    def _assessment(self):
        return self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": self.group.id,
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
            }
        )

    def test_closing_leaves_the_accounts_on_the_slip_with_a_purchase_return(self):
        """Sale 1000, purchase 500, purchase return 100, all at ICMS 18%.

        Booked balances before closing:
          payable    = 180 credit (the sale)
          recoverable =  90 debit (the purchase) - 18 (the return) = 72 debit

        The E110 balance due is 180 - (90 - 18) = 108. Closing must consume the
        72 the recoverable account actually holds, leaving 108 due in payable
        and ZERO in recoverable. Consuming the fiscal credit side (90) instead
        would credit more than the account holds and leave the asset negative.
        """
        self.init_invoice(
            "out_invoice",
            invoice_date="2026-07-10",
            amounts=[1000.0],
            taxes=self.sale_tax,
            post=True,
        )
        self.init_invoice(
            "in_invoice",
            invoice_date="2026-07-05",
            amounts=[500.0],
            taxes=self.purchase_tax,
            post=True,
        )
        self.init_invoice(
            "in_refund",
            invoice_date="2026-07-25",
            amounts=[100.0],
            taxes=self.purchase_tax,
            post=True,
        )

        # sanity: the invoices booked where we expect, before any closing
        self.assertAlmostEqual(self._book_balance(self.payable), -180.0, places=2)
        self.assertAlmostEqual(self._book_balance(self.receivable), 72.0, places=2)

        assessment = self._assessment()
        assessment.action_compute()
        self.assertAlmostEqual(assessment.debit_total, 180.0, places=2)
        self.assertAlmostEqual(assessment.credit_total, 90.0, places=2)
        self.assertAlmostEqual(assessment.credit_reversal_total, 18.0, places=2)
        self.assertAlmostEqual(assessment.assessed_balance, 108.0, places=2)
        self.assertAlmostEqual(assessment.amount_payable, 108.0, places=2)

        assessment.action_post()
        if assessment.move_id and assessment.move_id.state != "posted":
            assessment.move_id.action_post()

        # the recoverable account must NOT be driven negative by the closing
        self.assertGreaterEqual(
            self._book_balance(self.receivable),
            0.0,
            "closing drove the recoverable ICMS account into a negative asset",
        )
        # and the two accounts together must still show the slip: 108 to pay
        payable_balance = self._book_balance(self.payable)
        receivable_balance = self._book_balance(self.receivable)
        self.assertAlmostEqual(receivable_balance, 0.0, places=2)
        self.assertAlmostEqual(payable_balance, -108.0, places=2)
