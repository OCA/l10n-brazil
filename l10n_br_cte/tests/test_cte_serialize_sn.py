# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from .test_cte_serialize import TestCTeSerialize

_logger = logging.getLogger(__name__)


class TestCTeExportSN(TestCTeSerialize):
    def setUp(self):
        cte_list = [
            {
                "record_ref": "l10n_br_cte.demo_cte_sn_modal_aereo",
                "xml_file": "CTe35230905472475000102580200000602081550195716.xml",
            },
            {
                "record_ref": "l10n_br_cte.demo_cte_sn_modal_aquaviario",
                "xml_file": "CTe35231005472475000102580200000602161434590525.xml",
            },
        ]

        super().setUp(cte_list)

    def test_serialize_xml(self):
        for cte_data in self.cte_list:
            diff = self.serialize_xml(cte_data)
            _logger.info("Diff with expected XML (if any): %s" % (diff,))
            assert len(diff) == 0
