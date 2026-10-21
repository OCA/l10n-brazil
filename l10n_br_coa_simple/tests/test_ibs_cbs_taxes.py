# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_coa.tests.common import IbsCbsTaxesMixin


@tagged("post_install", "-at_install")
class TestIbsCbsTaxesSimple(IbsCbsTaxesMixin, TransactionCase):
    """The taxes of the simple chart use its own accounts, by exact code.

    IBS, CBS and IS go to the liability (2.1.4.02.11 to 13) and to the asset
    (1.1.2.05.11 to 13) of the chart. The deductible ones use the revenue
    deduction accounts of the group "3.1.2.01 IMPOSTOS S/ FATURAMENTO"
    (3.1.2.01.06 to 08), which are P&L accounts: the chart gives them the
    `income_other` type, the same one the generic chart uses for its
    "s/ Vendas" accounts.
    """

    chart_template = "br_oca_simple"
    tax_framework = "1"
    expected_accounts = {
        "tax_template_out_ibs": ("2.1.4.02.11", "1.1.2.05.11"),
        "tax_template_in_ibs": ("1.1.2.05.11", "2.1.4.02.11"),
        "tax_template_out_cbs": ("2.1.4.02.12", "1.1.2.05.12"),
        "tax_template_in_cbs": ("1.1.2.05.12", "2.1.4.02.12"),
        "tax_template_out_ibs_deductible": ("3.1.2.01.06", "3.1.2.01.06"),
        "tax_template_in_ibs_deductible": ("3.1.2.01.06", "2.1.4.02.11"),
        "tax_template_out_cbs_deductible": ("3.1.2.01.07", "3.1.2.01.07"),
        "tax_template_in_cbs_deductible": ("3.1.2.01.07", "2.1.4.02.12"),
        "tax_template_out_is": ("2.1.4.02.13", "1.1.2.05.13"),
        "tax_template_in_is": ("1.1.2.05.13", "2.1.4.02.13"),
        "tax_template_out_is_deductible": ("3.1.2.01.08", "3.1.2.01.08"),
        "tax_template_in_is_deductible": ("3.1.2.01.08", "2.1.4.02.13"),
    }

    def test_no_account_with_a_review_suffix_beside_the_chart_ones(self):
        codes = [
            account.code
            for account in self.env["account.account"]
            .with_company(self.company)
            .search([("company_ids", "in", self.company.id)])
        ]
        for code in codes:
            if code.endswith((".GEN", ".BR")):
                self.assertNotIn(code.rsplit(".", 1)[0], codes, code)
        self.assertFalse([code for code in codes if code.endswith(".BR")])

    def test_deductible_accounts_are_the_revenue_deduction_of_the_chart(self):
        """The accounts of the chart are reused: no `3.1.1.04.GEN` for them."""
        for code in ("3.1.2.01.06", "3.1.2.01.07", "3.1.2.01.08"):
            account = self._plan_account(code)
            self.assertEqual(account.account_type, "income_other", code)

    def test_migration_uses_the_revenue_deduction_of_the_chart(self):
        """A company loaded before gets the same accounts and type as a new one.

        Before this version the chart had these accounts as `liability_current`.
        """
        codes = ("3.1.2.01.06", "3.1.2.01.07", "3.1.2.01.08")
        for code in codes:
            self._plan_account(code).account_type = "liability_current"
        self._remove_new_taxes()

        self._migrate()

        self._assert_taxes_loaded()
        for code in codes:
            account = self._plan_account(code)
            self.assertEqual(account.account_type, "income_other", code)

    def _plan_account(self, code):
        account = (
            self.env["account.account"]
            .with_company(self.company)
            .search([("code", "=", code), ("company_ids", "in", self.company.id)])
        )
        self.assertEqual(len(account), 1, code)
        return account
