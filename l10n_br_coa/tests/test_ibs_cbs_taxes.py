# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from types import SimpleNamespace

from openupgradelib import openupgrade

from odoo.tests import TransactionCase, tagged

from .common import LOGGER_NAME, IbsCbsTaxesMixin, load_migration


@tagged("post_install", "-at_install")
class TestIbsCbsTaxes(IbsCbsTaxesMixin, TransactionCase):
    """The basic chart (`br_oca`) brings the taxes, but no account of its own.

    The generic and simple charts run the same tests with their exact
    accounts, in their own modules.
    """

    chart_template = "br_oca"

    def test_migration_links_the_tax_by_hand_with_the_module_of_the_chart(self):
        """The xmlid has the module the chart load would have used."""
        key = "tax_template_out_cbs_deductible"
        generated = self._tax(key)
        group = generated.tax_group_id
        generated.unlink()
        by_hand = self.env["account.tax"].create(
            {
                "name": "CBS feita a mao",
                "company_id": self.company.id,
                "tax_group_id": group.id,
                "type_tax_use": "sale",
                "deductible": True,
                "amount": 0.0,
            }
        )
        # Brazilian taxes added to another chart (`load_fiscal_taxes`) are
        # named in `l10n_br_coa`, not in `account`.
        self.company.chart_template = False

        with self.assertLogs(LOGGER_NAME, level="WARNING"):
            load_migration()._migrate_company(self.env, self.company)

        self.assertEqual(
            by_hand.get_external_id()[by_hand.id],
            f"l10n_br_coa.{self.company.id}_{key}",
        )

    def test_populate_without_the_chart_module(self):
        """The chart of the company may not be installed (or may not exist)."""
        company = self.env["res.company"].create(
            {
                "name": "Empresa sem plano",
                "country_id": self.env.ref("base.br").id,
                "currency_id": self.env.ref("base.BRL").id,
            }
        )
        self.assertNotIn(
            company.chart_template, self.chart._get_chart_template_mapping()
        )

        accounts = self.chart._populate_default_br_tax_accounts(
            company, only_tax_templates=["l10n_br_coa.tax_template_out_ibs"]
        )

        self.assertTrue(accounts)
        for key, account in accounts.items():
            xmlid = self.env["ir.model.data"].search(
                [
                    ("model", "=", "account.account"),
                    ("res_id", "=", account.id),
                    ("name", "=", f"{company.id}_{key}"),
                ]
            )
            self.assertEqual(xmlid.module, "l10n_br_coa", key)

    def test_flavor_follows_the_regime_and_the_chart(self):
        params = self.chart._get_br_tax_accounts_params
        company = self.company
        self.assertEqual(params(company, "br_oca_generic"), ("cfc", ".GEN"))
        self.assertEqual(params(company, "br_oca", tax_framework="3"), ("cfc", ".GEN"))
        self.assertEqual(params(company, "br_oca", tax_framework="1"), ("itg", ".GEN"))
        self.assertEqual(
            params(company, "br_oca_simple", tax_framework="1"), ("itg", ".GEN")
        )
        # Brazilian taxes added to a chart that is not Brazilian.
        self.assertEqual(params(company, "other_chart"), ("cfc", ".BR"))

    def test_migration_reads_the_regime_from_the_database(self):
        """The fiscal field is not loaded yet when this migration runs.

        The company stands in for the one the migration sees: no field in the
        registry, the column (when `l10n_br_fiscal` was ever installed) in the
        database.
        """
        migration = load_migration()
        stand_in = SimpleNamespace(id=self.company.id, _fields={})
        expected = False
        if openupgrade.column_exists(self.env.cr, "res_company", "tax_framework"):
            self.env.cr.execute(
                "UPDATE res_company SET tax_framework = '1' WHERE id = %s",
                (self.company.id,),
            )
            expected = "1"
        self.assertEqual(migration._tax_framework(self.env, stand_in), expected)
