# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDemoMainCompanyTaxCountry(TransactionCase):
    """The fiscal taxes of the demo main company must have the Brazilian country.

    Regression test for https://github.com/OCA/l10n-brazil/issues/5602
    account.tax.country_id is a stored computed field (depends only on
    company_id): it keeps the country the company had when the tax was
    created. The post_init_hook used to load the fiscal taxes on the demo
    base.main_company BEFORE switching it to Brazil, so the taxes stayed
    with country_id = United States and any fiscal document on that company
    failed account.move._validate_taxes_country.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_company = cls.env.ref("base.main_company")
        cls.brazil = cls.env.ref("base.br")

    def _main_company_fiscal_taxes(self):
        xmlid_data = (
            self.env["ir.model.data"]
            .sudo()
            .search(
                [
                    ("module", "=", "l10n_br_coa"),
                    ("model", "=", "account.tax"),
                    ("name", "=like", f"{self.main_company.id}\\_tax\\_template\\_%"),
                ]
            )
        )
        return self.env["account.tax"].browse(xmlid_data.mapped("res_id")).exists()

    def test_demo_main_company_fiscal_taxes_country(self):
        if not self.env.ref("base.module_l10n_br_account").demo:
            self.skipTest("the post_init_hook only loads these taxes with demo data")
        self.assertEqual(self.main_company.country_id, self.brazil)
        taxes = self._main_company_fiscal_taxes()
        self.assertTrue(
            taxes, "no fiscal tax loaded by the hook on the demo main company"
        )
        wrong_country = taxes.filtered(lambda tax: tax.country_id != self.brazil)
        self.assertFalse(
            wrong_country,
            "fiscal taxes of the demo main company with a country different"
            f" from Brazil: {wrong_country.mapped('name')}"
            f" ({wrong_country.mapped('country_id.name')})",
        )
