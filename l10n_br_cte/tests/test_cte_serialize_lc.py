# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from .test_cte_serialize import TestCTeSerialize

_logger = logging.getLogger(__name__)


class TestCTeExportLC(TestCTeSerialize):
    @classmethod
    def setUpClass(cls):
        cte_list = [
            {
                "record_ref": "l10n_br_cte.demo_cte_lc_modal_rodoviario",
                "xml_file": "CTe35240781583054000129570010000057311040645894.xml",
            },
            {
                "record_ref": "l10n_br_cte.demo_cte_lc_modal_aereo",
                "xml_file": "CTe35240781583054000129570010000057411040645890.xml",
            },
            {
                "record_ref": "l10n_br_cte.demo_cte_lc_modal_aquaviario",
                "xml_file": "CTe35240781583054000129570010000057511040645897.xml",
            },
            {
                "record_ref": "l10n_br_cte.demo_cte_lc_modal_ferroviario",
                "xml_file": "CTe35240781583054000129570010000057611040645893.xml",
            },
            {
                "record_ref": "l10n_br_cte.demo_cte_lc_modal_dutoviario",
                "xml_file": "CTe35240781583054000129570010000057711040645890.xml",
            },
        ]

        super().setUpClass(cte_list)

    def test_serialize_xml(self):
        for cte_data in self.cte_list:
            diff = self.serialize_xml(cte_data)
            _logger.info(f"Diff with expected XML (if any): {diff}")
            assert len(diff) == 0
