# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .test_nfse_serialize import TestNfseSerialize


class TestNfseExportSN(TestNfseSerialize):
    @classmethod
    def setUpClass(cls):
        nfse_list = [
            {
                "record_ref": "l10n_br_nfse_nacional.demo_nfse_sn",
                "xml_file": "dps-simples.xml",
            }
        ]
        super().setUpClass(nfse_list)

    def test_serialize_xml(self):
        for nfse_data in self.nfse_list:
            nfse_data[
                "nfse"
            ].document_key = "140015920176113500013200900000000000000006"
            nfse_data["nfse"].document_serie = "900"
            nfse_data["nfse"].document_number = "6"
            diff = self.serialize_xml(nfse_data)
            self.assertEqual(len(diff), 0)
