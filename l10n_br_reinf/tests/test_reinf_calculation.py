# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from psycopg2 import IntegrityError

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


class ReinfCalculationCommon(AccountMoveBRCommon):
    """Fixture of the calculation tests, with no test of its own.

    It is a class apart on purpose: a test class that inherits ANOTHER test
    class re-runs its tests under a different fixture, and that is how a suite
    starts asserting things nobody meant to assert.

    AccountMoveBRCommon gives a company with a Brazilian chart of accounts, so
    the invoices and the payments of these tests exist only inside the test.
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)
        cls.company = cls.env.company
        cls.company.reinf_environment = "2"
        cls.nature = cls.env.ref("l10n_br_reinf.nature_income_13002")
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "Reinf Supplier",
                "cnpj_cpf": "11.222.333/0001-81",
                "country_id": cls.env.ref("base.br").id,
                "is_company": True,
                "reinf_nature_income_id": cls.nature.id,
            }
        )
        cls.calculation_model = cls.env["l10n_br_reinf.calculation"]
        # Real taxes: the *_wh_value fields are re-derived from fiscal_tax_ids on
        # every write, so a value set by the fixture never survives the posting.
        cls.tax_irpj = cls._wh_tax("l10n_br_fiscal.tax_group_irpj_wh", 1.5)
        cls.tax_pis = cls._wh_tax("l10n_br_fiscal.tax_group_pis_wh", 0.65)
        cls.tax_cofins = cls._wh_tax("l10n_br_fiscal.tax_group_cofins_wh", 3.0)
        cls.tax_csll = cls._wh_tax("l10n_br_fiscal.tax_group_csll_wh", 1.0)

    @classmethod
    def _wh_tax(cls, fiscal_group_ref, percent):
        """A purchase tax that withholds, tied to a Brazilian fiscal group.

        The fiscal group is what says the tax is a withholding and which one it
        is, and it is how the calculation recognises the tax line.
        """
        fiscal_group = cls.env.ref(fiscal_group_ref)
        group = cls.env["account.tax.group"].create(
            {
                "name": f"Reinf {fiscal_group.name}",
                "fiscal_tax_group_id": fiscal_group.id,
            }
        )
        return cls.env["account.tax"].create(
            {
                "name": f"Reinf {fiscal_group.name}",
                "amount_type": "percent",
                "amount": -percent,
                "type_tax_use": "purchase",
                "tax_group_id": group.id,
                "company_id": cls.env.company.id,
            }
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _create_supplier_invoice(self, invoice_date, amount, partner=None, taxes=None):
        """A posted supplier invoice whose accounting carries the withholding."""
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": (partner or self.supplier).id,
                "invoice_date": invoice_date,
                "date": invoice_date,
                "company_id": self.company.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Service under withholding",
                            "quantity": 1,
                            "price_unit": amount,
                            "tax_ids": [(6, 0, [tax.id for tax in taxes or []])],
                        }
                    )
                ],
            }
        )
        move.invoice_line_ids.write({"reinf_nature_income_id": self.nature.id})
        move.action_post()
        return move

    def _pay(self, move, payment_date, amount=None):
        """Register a payment and reconcile it, which is what dates the PCC."""
        payable = move.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "partner_type": "supplier",
                "partner_id": move.commercial_partner_id.id,
                "amount": amount or move.amount_total,
                "date": payment_date,
                "company_id": self.company.id,
                "journal_id": self.company_data["default_journal_bank"].id,
            }
        )
        payment.action_post()
        payment_payable = payment.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        (payable | payment_payable).reconcile()
        return payment

    def _calculation(self, period):
        return self.calculation_model.create(
            {"company_id": self.company.id, "period": period}
        )


@tagged("post_install", "-at_install")
class TestReinfCalculation(ReinfCalculationCommon):
    def test_fg_date_is_per_tax_and_splits_competences(self):
        """Test 2 of the spec: invoice of July paid in August.

        The income tax is due on the credit and lands in July; PIS, COFINS and
        CSLL are due on the payment and land in August. Two competences, one
        invoice, and neither of them is wrong.
        """
        move = self._create_supplier_invoice(
            "2026-07-10",
            10000.0,
            taxes=[self.tax_irpj, self.tax_pis, self.tax_cofins, self.tax_csll],
        )
        self._pay(move, "2026-08-05")

        july = self._calculation("2026-07")
        july.action_compute()
        august = self._calculation("2026-08")
        august.action_compute()

        self.assertEqual(july.line_ids.mapped("tax"), ["irpj"])
        self.assertEqual(july.line_ids.fg_date, fields.Date.to_date("2026-07-10"))
        self.assertEqual(july.total_wh_amount, 150.0)
        self.assertTrue(july.line_ids.on_credit)

        self.assertEqual(
            sorted(set(august.line_ids.mapped("tax"))),
            ["cofins", "csll", "pis_pasep"],
        )
        self.assertEqual(
            set(august.line_ids.mapped("fg_date")),
            {fields.Date.to_date("2026-08-05")},
        )
        self.assertEqual(august.total_wh_amount, 465.0)
        self.assertFalse(any(august.line_ids.mapped("on_credit")))
        # The credit of another competence is explained, not hidden.
        self.assertIn("prior_period_invoice", august.exception_ids.mapped("reason"))

    def test_three_invoices_accumulate_in_the_competence(self):
        """Test 1 of the spec, on the calculation side: same supplier, same
        nature, three payments in the month."""
        for day in ("05", "15", "25"):
            move = self._create_supplier_invoice(
                f"2026-07-{day}", 1000.0, taxes=[self.tax_csll]
            )
            self._pay(move, f"2026-07-{day}")

        july = self._calculation("2026-07")
        july.action_compute()
        lines = july.line_ids
        self.assertEqual(len(lines), 3)
        self.assertEqual(set(lines.mapped("partner_id")), {self.supplier})
        self.assertEqual(set(lines.mapped("nature_income_id")), {self.nature})
        self.assertEqual(july.total_wh_amount, 30.0)
        self.assertEqual(len(set(lines.mapped("fg_date"))), 3)

    def test_partial_payment_is_proportional_and_flagged(self):
        """Paying half of an invoice withholds half of the PCC."""
        move = self._create_supplier_invoice(
            "2026-07-10", 1000.0, taxes=[self.tax_csll]
        )
        self._pay(move, "2026-07-20", amount=move.amount_total / 2)

        july = self._calculation("2026-07")
        july.action_compute()
        self.assertEqual(len(july.line_ids), 1)
        self.assertAlmostEqual(july.line_ids.wh_amount, 5.0, places=2)
        self.assertIn("partial_payment", july.exception_ids.mapped("reason"))

    def test_nature_missing_is_critical(self):
        """No nature of income, no declaration: it blocks and it says why."""
        unknown = self.env["res.partner"].create(
            {
                "name": "Supplier with no nature",
                "cnpj_cpf": "22.333.444/0001-81",
                "country_id": self.env.ref("base.br").id,
                "is_company": True,
            }
        )
        move = self._create_supplier_invoice(
            "2026-07-10", 1000.0, partner=unknown, taxes=[self.tax_irpj]
        )
        # Neither the line nor the partner says under which nature this income
        # is declared, and there is no service type to take it from.
        move.invoice_line_ids.write({"reinf_nature_income_id": False})
        self.assertFalse(move.invoice_line_ids.reinf_nature_income_id)

        july = self._calculation("2026-07")
        july.action_compute()
        self.assertFalse(july.line_ids)
        exception = july.exception_ids.filtered(
            lambda item: item.reason == "nature_missing"
        )
        self.assertTrue(exception)
        self.assertTrue(exception.critical)
        self.assertTrue(exception.advice)
        self.assertEqual(july.critical_exception_count, 1)

    def test_partner_without_cnpj_is_critical(self):
        partner = self.env["res.partner"].create(
            {"name": "No CNPJ", "is_company": True}
        )
        self._create_supplier_invoice(
            "2026-07-10", 1000.0, partner=partner, taxes=[self.tax_irpj]
        )
        july = self._calculation("2026-07")
        july.action_compute()
        self.assertIn("partner_without_cnpj", july.exception_ids.mapped("reason"))
        self.assertTrue(july.critical_exception_count)

    def test_compute_is_idempotent_and_keeps_verified_lines(self):
        """Recomputing rebuilds the lines but never throws away a manual check."""
        move = self._create_supplier_invoice(
            "2026-07-10", 1000.0, taxes=[self.tax_irpj]
        )
        july = self._calculation("2026-07")
        july.action_compute()
        self.assertEqual(len(july.line_ids), 1)
        total = july.total_wh_amount

        july.line_ids.write({"manually_verified": True, "note": "checked by hand"})
        july.action_compute()
        # The verified line survived and the recompute did not double it.
        self.assertEqual(len(july.line_ids), 2)
        self.assertEqual(
            july.line_ids.filtered("manually_verified").note, "checked by hand"
        )

        july.line_ids.filtered("manually_verified").unlink()
        # Nothing in the accounting changed between the runs: the recompute has
        # to find the very same invoice again.
        self.assertEqual(move.state, "posted")
        july.action_compute()
        self.assertEqual(len(july.line_ids), 1)
        # Whichever step of the cascade answered, the nature reached the line.
        self.assertEqual(july.line_ids.nature_income_id, self.nature)
        self.assertEqual(july.total_wh_amount, total)
        self.assertEqual(july.state, "computed")
        self.assertEqual(move.commercial_partner_id, july.line_ids.partner_id)

    def test_period_is_unique_per_company(self):
        self._calculation("2026-07")
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            with self.env.cr.savepoint():
                self._calculation("2026-07")
