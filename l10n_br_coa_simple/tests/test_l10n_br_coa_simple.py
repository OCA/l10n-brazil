# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.modules.migration import load_script
from odoo.tests.common import TransactionCase


class L10nBrSimpleCOA(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.l10n_br_coa_simple = cls.env.ref(
            "l10n_br_coa_simple.l10n_br_coa_simple_chart_template"
        )
        cls.l10n_br_company = cls.env["res.company"].create(
            {"name": "Empresa Teste do Plano de Contas Simplificado"}
        )

    def test_l10n_br_coa_simple(self):
        """Test installing the chart of accounts template in a new company"""
        self.l10n_br_coa_simple.try_loading(company=self.l10n_br_company)
        self.assertEqual(
            self.l10n_br_coa_simple, self.l10n_br_company.chart_template_id
        )

    def test_migration_updates_existing_accounts(self):
        self.l10n_br_coa_simple.try_loading(company=self.l10n_br_company)

        def account(code):
            return self.env.ref(
                f"l10n_br_coa_simple.{self.l10n_br_company.id}_account_template_{code}"
            )

        taxes = self.env.ref("l10n_br_coa.account_tag_dva_taxes")
        federal = self.env.ref("l10n_br_coa.account_tag_dva_taxes_federal")
        account("3120109").unlink()
        account("3120107").tag_ids -= federal
        account("3120202").tag_ids |= taxes
        migration = load_script(
            "l10n_br_coa_simple/migrations/16.0.2.3.0/post-migration.py", "mig"
        )
        migration.migrate(self.env.cr, "16.0.2.2.0")
        migration.migrate(self.env.cr, "16.0.2.2.0")
        self.assertEqual(account("3120109").code, "3.1.2.01.09")
        self.assertIn(federal, account("3120107").tag_ids)
        self.assertNotIn(taxes, account("3120202").tag_ids)
