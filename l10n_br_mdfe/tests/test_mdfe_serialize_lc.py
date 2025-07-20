# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from .test_mdfe_serialize import TestMDFeSerialize

_logger = logging.getLogger(__name__)


class TestMDFeExportLC(TestMDFeSerialize):
    @classmethod
    def setUpClass(cls):
        mdfe_list = [
            {
                "record_ref": "l10n_br_mdfe.demo_mdfe_lc_modal_ferroviario",
                "xml_file": "MDFe35230905472475000102580200000602011208018449.xml",
            },
            {
                "record_ref": "l10n_br_mdfe.demo_mdfe_lc_modal_rodoviario",
                "xml_file": "MDFe35230905472475000102580200000602071611554500.xml",
            },
        ]
        super().setUpClass(mdfe_list)

    def test_serialize_xml(self):
        for mdfe_data in self.mdfe_list:
            diff = self.serialize_xml(mdfe_data)
            _logger.info(f"Diff with expected XML (if any): {diff}")
            assert len(diff) == 0
