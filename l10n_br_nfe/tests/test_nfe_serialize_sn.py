# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_nfe_serialize import TestNFeExport


class TestNFeExportSN(TestNFeExport):
    def setUp(self):
        super().setUp()

        self.nfe_list = [
            {
                "record_id": self.env.ref(
                    "l10n_br_nfe.demo_nfe_national_sale_for_same_state"
                ),
                "xml_file": "NFe35200159594315000157550010000000012062777161.xml",
            }
        ]
