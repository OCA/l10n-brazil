# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from .test_cte_serialize import TestCTeSerialize

_logger = logging.getLogger(__name__)


class TestCTeExportSN(TestCTeSerialize):
    def setUp(self):
        cte_list = [
            {
                "record_ref": "l10n_br_cte.demo_cte_sn_modal_rodoviario",
                "xml_file": "CTe35240759594315000157570010000057311040445890.xml",
            },
        ]

        super().setUp(cte_list)

    def test_serialize_xml(self):
        for cte_data in self.cte_list:
            diff = self.serialize_xml(cte_data)
            _logger.info("Diff with expected XML (if any): %s" % (diff,))
            assert len(diff) == 0
