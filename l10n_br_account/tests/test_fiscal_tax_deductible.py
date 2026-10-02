# Copyright 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase


class TestFiscalTaxDeductible(TransactionCase):
    """`account_taxes` has to answer for the company it was asked about.

    `l10n_br_fiscal.operation.deductible_taxes` is company dependent, so
    reading it depends on the company in the environment unless somebody says
    otherwise. Every caller of `account_taxes` passes the company of its own
    document, and the answer has to follow that company: a purchase line of
    company A cannot take the deductible taxes just because the user happened
    to have company B selected.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company_a = cls.env["res.company"].create({"name": "Deductible on"})
        cls.company_b = cls.env["res.company"].create({"name": "Deductible off"})
        cls.env.user.company_ids += cls.company_a + cls.company_b
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        # The key is company dependent: switch company to write each value.
        cls.operation.with_company(cls.company_a).deductible_taxes = True
        cls.operation.with_company(cls.company_b).deductible_taxes = False

        cls.fiscal_tax = cls.env.ref("l10n_br_fiscal.tax_pis_0_65")
        group = cls.fiscal_tax.tax_group_id.account_tax_group()
        # One plain tax and one deductible tax in company A, so the answer can
        # actually differ. Without the deductible one there would be nothing to
        # tell apart and the test would pass for the wrong reason.
        cls.plain_tax = cls.env["account.tax"].create(
            {
                "name": "PIS purchase",
                "amount_type": "percent",
                "amount": 0.65,
                "type_tax_use": "purchase",
                "tax_group_id": group.id,
                "company_id": cls.company_a.id,
                "deductible": False,
            }
        )
        cls.deductible_tax = cls.env["account.tax"].create(
            {
                "name": "PIS purchase deductible",
                "amount_type": "percent",
                "amount": 0.65,
                "type_tax_use": "purchase",
                "tax_group_id": group.id,
                "company_id": cls.company_a.id,
                "deductible": True,
            }
        )

    def _account_taxes_for(self, company, env_company):
        """Ask about `company` from an environment sitting on `env_company`."""
        fiscal_tax = self.fiscal_tax.with_company(env_company)
        return fiscal_tax.account_taxes(
            user_type="purchase",
            fiscal_operation=self.operation,
            company=company,
        )

    def test_the_company_asked_about_decides_the_deductible_tax(self):
        """Company A deducts, so asking about A brings the deductible tax."""
        taxes = self._account_taxes_for(self.company_a, self.company_a)
        self.assertIn(self.plain_tax, taxes)
        self.assertIn(self.deductible_tax, taxes)

    def test_the_environment_company_does_not_decide_it(self):
        """This is the regression: same question, different environment.

        Asking about company A from an environment on company B used to drop
        the deductible tax, because the company dependent key was read for B.
        """
        from_a = self._account_taxes_for(self.company_a, self.company_a)
        from_b = self._account_taxes_for(self.company_a, self.company_b)
        self.assertEqual(from_a, from_b)
        self.assertIn(self.deductible_tax, from_b)

    def test_a_company_that_does_not_deduct_never_takes_the_deductible_tax(self):
        """The fix must not turn the flag on for everybody."""
        self.operation.with_company(self.company_a).deductible_taxes = False
        taxes = self._account_taxes_for(self.company_a, self.company_a)
        self.assertIn(self.plain_tax, taxes)
        self.assertNotIn(self.deductible_tax, taxes)

    def test_without_a_company_the_operation_answers_for_its_own_company(self):
        """Caller that passes no company keeps the old behaviour.

        With no company to follow, the answer comes from the company the
        operation record itself is in, which is what it did before.
        """
        taxes = self.fiscal_tax.with_company(self.company_a).account_taxes(
            user_type="purchase",
            fiscal_operation=self.operation.with_company(self.company_a),
        )
        self.assertIn(self.deductible_tax, taxes)
