# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged

# Tax -> (invoice account, refund account) of the chart, by exact code.
EXPECTED_ACCOUNTS = {
    "tax_template_out_icms": ("2.1.7.1.03", "1.1.4.1.02"),
    "tax_template_in_icms": ("1.1.4.1.02", "2.1.7.1.03"),
    "tax_template_out_pis": ("2.1.7.1.05", "1.1.4.1.05"),
    "tax_template_icms_out_deductible": ("6.1.1.2.03", "6.1.1.2.23"),
}


@tagged("post_install", "-at_install")
class TestTaxAccountsCompany(TransactionCase):
    """The default tax accounts are the ones of the chart, in the new company.

    The code of an account belongs to a company. The search for the account of
    the chart ran in the company of the user instead of the one being loaded,
    so the account was never found and a copy with the review suffix (`.GEN`,
    `.BR`) was created beside it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The user company is NOT the one being loaded: this is what makes the
        # search look at the wrong company.
        cls.user_company = cls.env.company
        cls.chart = cls.env["account.chart.template"]
        cls.company = cls._create_company("Empresa Plano Genérico")

    @classmethod
    def _create_company(cls, name, **vals):
        company = cls.env["res.company"].create(
            {
                "name": name,
                "country_id": cls.env.ref("base.br").id,
                "currency_id": cls.env.ref("base.BRL").id,
                **vals,
            }
        )
        cls.env.user.company_ids |= company
        return company

    def _tax(self, company, key):
        for module in ("account", "l10n_br_coa"):
            tax = self.env.ref(f"{module}.{company.id}_{key}", raise_if_not_found=False)
            if tax:
                return tax
        return self.env["account.tax"]

    def _tax_account_codes(self, company, key):
        tax = self._tax(company, key)
        self.assertTrue(tax, f"{key} was not loaded")
        codes = []
        for lines in (
            tax.invoice_repartition_line_ids,
            tax.refund_repartition_line_ids,
        ):
            line = lines.filtered(lambda line: line.repartition_type == "tax")
            codes.append(line.account_id.with_company(company).code)
        return tuple(codes)

    def _codes(self, company):
        accounts = (
            self.env["account.account"]
            .with_company(company)
            .search([("company_ids", "in", company.id)])
        )
        return accounts.mapped("code")

    def _assert_no_duplicates(self, company):
        codes = self._codes(company)
        for code in codes:
            if code.endswith((".GEN", ".BR")):
                base = code.rsplit(".", 1)[0]
                self.assertNotIn(
                    base, codes, f"{code} was created beside the account {base}"
                )
        self.assertFalse(
            [code for code in codes if code.endswith(".BR")],
            "no account with the .BR suffix is expected on a chart company",
        )

    def test_taxes_use_the_chart_accounts(self):
        self.chart.try_loading("br_oca_generic", self.company, install_demo=False)
        self.assertEqual(self.company.chart_template, "br_oca_generic")
        for key, expected in EXPECTED_ACCOUNTS.items():
            self.assertEqual(self._tax_account_codes(self.company, key), expected, key)
        self._assert_no_duplicates(self.company)

    def test_populate_twice_creates_nothing(self):
        """Running the helper again finds what the first run left."""
        self.chart.try_loading("br_oca_generic", self.company, install_demo=False)
        before = sorted(self._codes(self.company))
        self.chart._populate_default_br_tax_accounts(self.company, flavor="cfc")
        self.assertEqual(sorted(self._codes(self.company)), before)
        for key, expected in EXPECTED_ACCOUNTS.items():
            self.assertEqual(self._tax_account_codes(self.company, key), expected, key)

    def test_branch_uses_the_accounts_of_the_parent(self):
        """A branch loads no accounts: it shares the ones of its parent."""
        self.chart.try_loading("br_oca_generic", self.company, install_demo=False)
        before = sorted(self._codes(self.company))
        branch = self._create_company(
            "Filial Plano Genérico", parent_id=self.company.id
        )
        self.chart.try_loading("br_oca_generic", branch, install_demo=False)
        self.assertEqual(sorted(self._codes(self.company)), before)
        self._assert_no_duplicates(self.company)
        # The taxes are the ones of the parent; the branch has none of its own.
        self.assertFalse(
            self.env["account.tax"].search_count([("company_id", "=", branch.id)])
        )

    def test_branch_leaves_no_unused_xmlids(self):
        """The load of a branch creates no tax or account xmlid for it."""
        self.chart.try_loading("br_oca_generic", self.company, install_demo=False)
        branch = self._create_company("Filial Sem Xmlids", parent_id=self.company.id)
        self.chart.try_loading("br_oca_generic", branch, install_demo=False)
        leftovers = self.env["ir.model.data"].search(
            [
                ("model", "in", ("account.tax", "account.account")),
                ("name", "=like", f"{branch.id}\\_%"),
            ]
        )
        self.assertFalse(leftovers.mapped("complete_name"))
