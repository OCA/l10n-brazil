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
        self._add_line(a, "debit", 40.0, code="SP010001")
        self._add_line(a, "credit", 30.0, code="SP020001")
        self._add_line(a, "credit", 25.0, code="SP030001")

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

    def test_closing_move_is_balanced_and_uses_group_accounts(self):
        """The entry balances and uses the accounts the core already models."""
        self._configure_group()
        a = self._new_assessment()
        a.action_compute()
        self._add_line(a, "debit", 1000.0)
        self._add_line(a, "credit", 250.0)
        a.action_post()

        self.assertEqual(a.state, "posted")
        move = a.move_id
        self.assertTrue(move)
        self.assertAlmostEqual(
            sum(move.line_ids.mapped("debit")),
            sum(move.line_ids.mapped("credit")),
            places=2,
            msg="the closing entry has to balance",
        )
        contas = move.line_ids.mapped("account_id")
        self.assertIn(self.account_payable, contas)
        self.assertIn(self.account_receivable, contas)
        # 750 due: credit the recoverable account, debit the payable one
        linha_pagar = move.line_ids.filtered(
            lambda line: line.account_id == self.account_payable
        )
        self.assertAlmostEqual(linha_pagar.debit, 750.0, places=2)

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
        self._add_line(a, "debit", 500.0)
        a.action_post()
        self.assertTrue(a.move_id)
        a.action_draft()
        self.assertEqual(a.state, "draft")
        self.assertFalse(a.move_id)


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
        self.assertEqual(assessment.state, "computed")
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
