# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.modules.migration import load_script
from odoo.tests.common import TransactionCase


class L10nBrCoaGeneric(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.l10n_br_company = cls.env["res.company"].create(
            {"name": "Empresa Teste do Plano de Contas CFC"}
        )

    def test_l10n_br_coa_generic(self):
        """Test installing the chart of accounts template in a new company"""

        chart_template = self.env["account.chart.template"]
        chart_template.try_loading(
            "br_oca_generic", self.l10n_br_company, install_demo=True
        )

        # Verify the chart template was loaded
        self.assertEqual(self.l10n_br_company.chart_template, "br_oca_generic")

        # Verify anglo saxon accounting is enabled
        self.assertTrue(self.l10n_br_company.anglo_saxon_accounting)

    def test_migration_updates_existing_accounts(self):
        self.env["account.chart.template"].try_loading(
            "br_oca_generic", self.l10n_br_company, install_demo=True
        )

        def account(code):
            # Odoo 18.0: the account code is stored per company
            return self.env.ref(
                f"account.{self.l10n_br_company.id}_coa_generic_{code}"
            ).with_company(self.l10n_br_company)

        taxes = self.env.ref("l10n_br_coa.account_tag_dva_taxes")
        state = self.env.ref("l10n_br_coa.account_tag_dva_taxes_state")
        inputs = self.env.ref("l10n_br_coa.account_tag_dva_inputs")
        account("511207").unlink()
        account("611203").tag_ids -= state
        account("611301").tag_ids |= taxes
        account("511701").tag_ids |= inputs
        migration = load_script(
            "l10n_br_coa_generic/migrations/18.0.2.3.0/post-migration.py", "mig"
        )
        migration.migrate(self.env.cr, "18.0.2.2.0")
        migration.migrate(self.env.cr, "18.0.2.2.0")
        self.assertEqual(account("511207").code, "5.1.1.2.07")
        self.assertIn(state, account("611203").tag_ids)
        self.assertNotIn(taxes, account("611301").tag_ids)
        self.assertNotIn(inputs, account("511701").tag_ids)
