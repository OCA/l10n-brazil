# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from .test_nfe_serialize import TestNFeExport

_logger = logging.getLogger(__name__)


class TestNFeExportLC(TestNFeExport):
    def setUp(self):
        nfe_list = [
            {
                "record_ref": "l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11",
                "xml_file": "NFe35200159594315000157550010000000022062777169.xml",
            },
            {
                "record_ref": "l10n_br_nfe.demo_nfe_natural_icms_7_resale",
                "xml_file": "NFe35200159594315000157550010000000032062777166.xml",
            },
        ]
        super().setUp(nfe_list)

    def test_serialize_xml(self):
        for nfe_data in self.nfe_list:
            diff = self.serialize_xml(nfe_data)
            _logger.info(f"Diff with expected XML (if any): {diff}")
            assert len(diff) == 0
