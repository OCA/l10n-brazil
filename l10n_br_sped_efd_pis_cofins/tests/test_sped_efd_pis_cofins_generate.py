# Copyright 2026 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from datetime import date

from odoo.tests import common


class SpedEfdPisCofinsGenerateTest(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].search(
            [("name", "=", "Empresa Lucro Presumido")], limit=1
        )

    def _authorize_documents(self):
        documents = self.env["l10n_br_fiscal.document"].search(
            [("company_id", "=", self.company.id)]
        )
        for index, document in enumerate(documents):
            vals = {}
            if not document.document_date:
                vals["document_date"] = date(2024, 1, 10 + index)
                vals["date_in_out"] = date(2024, 1, 10 + index)
            if not document.document_number:
                vals["document_number"] = str(1000 + document.id)
            if not document.document_serie:
                vals["document_serie"] = "1"
            if vals:
                document.write(vals)
        documents.write({"state_edoc": "autorizada"})
        return documents

    def test_generate_efd_pis_cofins(self):
        if not self.company:
            self.skipTest("demo company 'Empresa Lucro Presumido' not available")
        documents = self._authorize_documents()
        if not documents:
            self.skipTest("no fiscal documents in demo data")

        model = self.env["l10n_br_sped.efd_pis_cofins.0000"].with_company(self.company)
        vals = model._map_from_odoo(self.company, None, None)
        vals.update(
            {
                "company_id": self.company.id,
                "DT_INI": date(2024, 1, 1),
                "DT_FIN": date(2024, 1, 31),
            }
        )
        declaration = model.create(vals)
        declaration.button_populate_sped_from_odoo()
        text = declaration._generate_sped_text()

        self.assertTrue(text.startswith("|0000|"))
        # regime, documents/items and the cumulative PIS/COFINS apuration
        self.assertIn("\n|0110|", text)
        self.assertIn("\n|C100|", text)
        self.assertIn("\n|C170|", text)
        self.assertIn("\n|M200|", text)
        self.assertIn("\n|M210|", text)
        self.assertIn("\n|M600|", text)
        self.assertIn("\n|M610|", text)
