# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_nfe_serialize import TestNFeExport


class TestNFeExportLC(TestNFeExport):
    def setUp(self):
        super().setUp()

        self.nfe_list = [
            {
                "record_id": self.env.ref(
                    "l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11"
                ),
                "xml_file": "NFe35210681583054000129550010000000011760018069.xml",
            },
            {
                "record_id": self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale"),
                "xml_file": "NFe35210681583054000129550010000000021760023175.xml",
            },
        ]
