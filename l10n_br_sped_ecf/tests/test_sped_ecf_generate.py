# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from datetime import date

from odoo.tests import common


class SpedEcfGenerateTest(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].search(
            [("name", "=", "Empresa Lucro Presumido")], limit=1
        )

    def _fiscal_year(self):
        lines = self.env["account.move.line"].search(
            [
                ("company_id", "=", self.company.id),
                ("parent_state", "=", "posted"),
                ("account_id", "!=", False),
                ("date", "!=", False),
            ]
        )
        dates = lines.mapped("date")
        if not dates:
            return None, None
        return date(min(dates).year, 1, 1), date(max(dates).year, 12, 31)

    def test_generate_ecf(self):
        if not self.company:
            self.skipTest("demo company 'Empresa Lucro Presumido' not available")
        if not self.company.legal_nature_id:
            self.company.legal_nature_id = self.env[
                "l10n_br_fiscal.legal.nature"
            ].search([], limit=1)
        if not self.company.cnae_main_id:
            self.company.cnae_main_id = self.env["l10n_br_fiscal.cnae"].search(
                [], limit=1
            )
        dt_ini, dt_fin = self._fiscal_year()
        if not dt_ini:
            self.skipTest("no posted account moves in demo data")

        model = self.env["l10n_br_sped.ecf.0000"].with_company(self.company)
        vals = model._map_from_odoo(self.company, None, None)
        vals.update({"company_id": self.company.id, "DT_INI": dt_ini, "DT_FIN": dt_fin})
        declaration = model.create(vals)
        declaration.button_populate_sped_from_odoo()
        text = declaration._generate_sped_text()

        self.assertTrue(text.startswith("|0000|"))
        # identification, chart of accounts, balances and apuration periods
        self.assertIn("\n|0010|", text)
        self.assertIn("\n|J050|", text)
        self.assertIn("\n|K155|", text)
        self.assertIn("\n|P030|", text)
