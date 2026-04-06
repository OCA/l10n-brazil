from .test_nfse_serialize import TestNfseSerialize

class TestNfseExportLC(TestNfseSerialize):
    @classmethod
    def setUpClass(cls):
        nfse_list = [{
            "record_ref": "l10n_br_nfse_nacional.demo_nfse_lc",
            "xml_file": "dps-regime-normal.xml",
        }]
        super().setUpClass(nfse_list)

    def test_serialize_xml(self):
        for nfse_data in self.nfse_list:
            nfse_data["nfse"].document_key = "42024042000000000000000000700000000000002"
            nfse_data["nfse"].document_serie = "00007"
            nfse_data["nfse"].document_number = "2"
            diff = self.serialize_xml(nfse_data)
            self.assertEqual(len(diff), 0)
