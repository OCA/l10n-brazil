from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from ..models.account_chart_template import DEFAULT_TAX_ACCOUNTS


@tagged("post_install", "-at_install")
class TestCoaLoad(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(
        cls, chart_template_ref="l10n_generic_coa.configurable_chart_template"
    ):
        super().setUpClass(chart_template_ref=None)

        cls.company = cls.env["res.company"].create(
            {
                "name": "Brazilian Test Company",
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.env.user.company_ids = [(4, cls.company.id)]
        cls.env.user.company_id = cls.company

        cls.chart = cls.env.ref(chart_template_ref)
        cls.chart.with_context(allowed_company_ids=[cls.company.id]).try_loading(
            company=cls.company
        )

    def test_load_and_populate_coa(self):
        # Manually call and verify _populate_default_br_tax_accounts
        # This call is normally done from l10n_br_account, so we simulate it here
        # to test the method in isolation within the l10n_br_coa module.
        self.chart.with_company(self.company)._populate_default_br_tax_accounts(
            self.company, flavor="cfc", review_suffix=""
        )

        Account = self.env["account.account"]

        # Verify account creation from DEFAULT_TAX_ACCOUNTS
        icms_payable_data = DEFAULT_TAX_ACCOUNTS["tax_icms_payable"]
        icms_payable_account = Account.search(
            [
                ("code", "=", icms_payable_data[0]),
                ("company_id", "=", self.company.id),
            ]
        )
        self.assertEqual(
            len(icms_payable_account), 1, "ICMS a Recolher account was not created."
        )
        self.assertEqual(icms_payable_account.name, icms_payable_data[2])
        self.assertEqual(icms_payable_account.account_type, icms_payable_data[3])

        icms_receivable_data = DEFAULT_TAX_ACCOUNTS["tax_icms_receivable"]
        icms_receivable_account = Account.search(
            [
                ("code", "=", icms_receivable_data[0]),
                ("company_id", "=", self.company.id),
            ]
        )
        self.assertEqual(
            len(icms_receivable_account), 1, "ICMS a Compensar account was not created."
        )
