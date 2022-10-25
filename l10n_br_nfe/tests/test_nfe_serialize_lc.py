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
                "xml_file": "NFe35200159594315000157550010000000022062777169.xml",
            },
            {
                "record_id": self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale"),
                "xml_file": "NFe35200159594315000157550010000000032062777166.xml",
            },
        ]
