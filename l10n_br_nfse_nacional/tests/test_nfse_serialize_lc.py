# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .test_nfse_serialize import TestNfseSerialize


class TestNfseExportLC(TestNfseSerialize):
    @classmethod
    def setUpClass(cls):
        nfse_list = [
            {
                "record_ref": "l10n_br_nfse_nacional.demo_nfse_lc",
                "xml_file": "dps-regime-normal.xml",
            }
        ]
        super().setUpClass(nfse_list)

    def test_serialize_xml(self):
        for nfse_data in self.nfse_list:
            nfse_data[
                "nfse"
            ].document_key = "420240420000000000000000007000000000000002"
            nfse_data["nfse"].document_serie = "00007"
            nfse_data["nfse"].document_number = "2"
            diff = self.serialize_xml(nfse_data)
            self.assertEqual(len(diff), 0)

    def test_dhemi_matches_local_timezone(self):
        nfse = self.nfse_list[0]["nfse"]
        self.assertEqual(nfse.nfse10_dhEmi, "2023-09-09T09:42:06-03:00")
