# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestPreviousPeriods(AccountMoveBRCommon):
    """The start of the assessment by the system, and the credit balance chain
    from one month to the next, against posted supplier bills."""

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.configure_normal_company_taxes()
        cls.company = cls.company_data["company"]
        # the ICMS of the input becomes recoverable, so the bill books it
        cls.env.ref("l10n_br_fiscal.fo_compras").deductible_taxes = True
        cls.icms_group = cls.env.ref("l10n_br_coa.tax_group_icms")

    def _purchase(self, number, invoice_date):
        return self.init_invoice(
            "in_invoice",
            products=[self.product_a],
            invoice_date=invoice_date,
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[self.env.ref("l10n_br_fiscal.fo_compras_compras")],
            document_serie="1",
            document_number=number,
            post=True,
        )

    def _configure_closing_accounts(self):
        group = self.icms_group.with_company(self.company)
        if (
            group.property_tax_payable_account_id
            and group.property_tax_receivable_account_id
        ):
            return
        accounts = {
            "property_tax_payable_account_id": ("ICMSPAY", "liability_current"),
            "property_tax_receivable_account_id": ("ICMSREC", "asset_current"),
        }
        group.write(
            {
                field: self.env["account.account"]
                .create(
                    {
                        "name": code,
                        "code": code,
                        "account_type": account_type,
                        "company_id": self.company.id,
                    }
                )
                .id
                for field, (code, account_type) in accounts.items()
            }
        )

    def _assess(self, month, post=True):
        assessment = self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": self.icms_group.id,
                "date_from": date(2026, month, 1),
                "date_to": date(2026, month, 28),
            }
        )
        assessment.action_compute()
        if post:
            self._configure_closing_accounts()
            assessment.action_post()
        return assessment

    def _old_base(self):
        for number, when in (
            ("701", date(2024, 6, 10)),
            ("702", date(2025, 6, 10)),
            ("601", date(2026, 6, 10)),
            ("602", date(2026, 7, 10)),
        ):
            self._purchase(number, when)

    def test_the_bill_books_the_icms_the_assessment_reads(self):
        """Guard for the tests below: without a recoverable ICMS on the bill
        there is no earlier movement to find."""
        bill = self._purchase("600", date(2026, 7, 10))
        assessment = self.env["l10n_br_tax.assessment"].new(
            {"company_id": self.company.id, "tax_group_id": self.icms_group.id}
        )
        self.assertTrue(
            bill.line_ids.filtered(
                lambda line: line.tax_line_id in assessment._get_taxes()
            )
        )

    def test_an_existing_base_without_the_start_is_asked_for_it(self):
        self._old_base()
        self.assertFalse(self.company.tax_assessment_start)
        with self.assertRaises(UserError) as error:
            self._assess(7, post=False)
        message = error.exception.args[0]
        self.assertIn("Defina o início da apuração pelo sistema", message)
        self.assertIn("Empresas > aba Fiscal", message)
        self.assertFalse(self.company.tax_assessment_start)

    def test_a_new_base_starts_in_the_month_of_the_first_assessment(self):
        self.assertFalse(self.company.tax_assessment_start)
        self._purchase("602", date(2026, 7, 10))
        self._assess(7, post=False)
        self.assertEqual(self.company.tax_assessment_start, date(2026, 7, 1))

    def test_the_start_is_the_first_day_of_a_month(self):
        with self.assertRaises(ValidationError):
            self.company.tax_assessment_start = date(2026, 6, 15)

    def test_the_informed_opening_balance_is_the_first_previous_balance(self):
        self._purchase("602", date(2026, 7, 10))
        self.company.tax_assessment_start = date(2026, 7, 1)
        opening = self.env["l10n_br_tax.assessment.opening"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": self.icms_group.id,
                "amount": 1234.56,
            }
        )
        self.assertEqual(opening.informed_by, self.env.user)
        july = self._assess(7, post=False)
        self.assertFalse(july.previous_assessment_id)
        self.assertEqual(july.previous_balance, 1234.56)

    def test_the_opening_balance_is_not_added_after_the_first_period(self):
        self._purchase("601", date(2026, 6, 10))
        self._purchase("602", date(2026, 7, 10))
        self.company.tax_assessment_start = date(2026, 6, 1)
        self.env["l10n_br_tax.assessment.opening"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": self.icms_group.id,
                "amount": 1000.0,
            }
        )
        june = self._assess(6)
        july = self._assess(7, post=False)
        self.assertEqual(july.previous_assessment_id, june)
        self.assertEqual(july.previous_balance, june.amount_carried_forward)

    def test_the_assessment_warns_of_an_earlier_month_with_movement(self):
        self.company.tax_assessment_start = date(2026, 6, 1)
        self._purchase("601", date(2026, 6, 10))
        self._purchase("602", date(2026, 7, 10))
        july = self._assess(7, post=False)
        self.assertIn("06/2026", july.previous_periods_warning)
        with self.assertRaises(UserError) as error:
            july._check_previous_periods()
        self.assertIn("06/2026", error.exception.args[0])

    def test_there_is_no_warning_when_the_earlier_month_is_posted(self):
        self.company.tax_assessment_start = date(2026, 6, 1)
        self._purchase("601", date(2026, 6, 10))
        self._purchase("602", date(2026, 7, 10))
        self._assess(6)
        july = self._assess(7, post=False)
        self.assertFalse(july.previous_periods_warning)
        july._check_previous_periods()

    def test_a_computed_earlier_month_is_not_enough(self):
        self.company.tax_assessment_start = date(2026, 6, 1)
        self._purchase("601", date(2026, 6, 10))
        self._purchase("602", date(2026, 7, 10))
        self._assess(6, post=False)
        july = self._assess(7, post=False)
        self.assertIn("06/2026", july.previous_periods_warning)

    def test_a_month_without_movement_does_not_have_to_be_assessed(self):
        self.company.tax_assessment_start = date(2026, 6, 1)
        self._purchase("602", date(2026, 7, 10))
        july = self._assess(7, post=False)
        self.assertFalse(july.previous_periods_warning)
        july._check_previous_periods()

    def test_with_the_start_only_the_months_from_it_are_listed(self):
        self._old_base()
        self.company.tax_assessment_start = date(2026, 6, 1)
        july = self._assess(7, post=False)
        self.assertIn("06/2026", july.previous_periods_warning)
        self.assertNotIn("2024", july.previous_periods_warning)
        self.assertNotIn("2025", july.previous_periods_warning)

    def test_without_the_start_the_check_asks_for_it(self):
        self._old_base()
        july = self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": self.icms_group.id,
                "date_from": date(2026, 7, 1),
                "date_to": date(2026, 7, 28),
            }
        )
        self.assertIn(
            "Defina o início da apuração pelo sistema", july.previous_periods_warning
        )
        with self.assertRaises(UserError):
            july._check_previous_periods()

    def test_the_company_form_shows_the_start(self):
        view = self.env["res.company"].get_view(
            self.env.ref("l10n_br_fiscal.fiscal_res_company_form").id
        )
        self.assertIn("tax_assessment_start", view["arch"])
