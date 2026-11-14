# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestFiscalDashboards(TransactionCase):
    def test_dashboards(self):
        """The dashboards only use fields of the fiscal analysis and open."""
        report = self.env["l10n_br_fiscal.document.line.report"]
        for xmlid in (
            "dashboard_fiscal",
            "dashboard_fiscal_assessment",
            "dashboard_tax_reform",
        ):
            dashboard = self.env.ref(f"l10n_br_fiscal_spreadsheet_dashboard.{xmlid}")
            data = json.loads(dashboard.spreadsheet_data)
            fields = set()
            for pivot in data["pivots"].values():
                self.assertEqual(pivot["model"], report._name)
                fields |= {m["fieldName"] for m in pivot["measures"]}
                for group in pivot["rows"] + pivot["columns"]:
                    fields.add(group["fieldName"].split(":")[0])
                for matching in pivot["fieldMatching"].values():
                    fields.add(matching["chain"])
            self.assertFalse(fields - set(report._fields), xmlid)
            self.assertTrue(dashboard.get_readonly_dashboard()["snapshot"])
