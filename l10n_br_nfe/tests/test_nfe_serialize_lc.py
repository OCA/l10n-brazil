# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from .test_nfe_serialize import TestNFeExport

_logger = logging.getLogger(__name__)


class TestNFeExportLC(TestNFeExport):
    @classmethod
    def setUpClass(cls):
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
        super().setUpClass(nfe_list)

    @classmethod
    def prepare_test_nfe(cls, nfe):
        # the Odoo 19 demo data gives a barcode to the Flipover product; the
        # expected XML files were generated without it (cEAN SEM GTIN)
        nfe.fiscal_line_ids.product_id.barcode = False
        # with the demo data this partner is created before l10n_br_fiscal
        # adds ind_ie_dest, so it keeps the column default "1" that the
        # expected XML files carry; created later it would be computed as "9"
        if nfe.partner_id == cls.env.ref("l10n_br_base.res_partner_cliente11_sp"):
            nfe.partner_id.ind_ie_dest = "1"
        return super().prepare_test_nfe(nfe)

    def test_serialize_xml(self):
        for nfe_data in self.nfe_list:
            diff = self.serialize_xml(nfe_data)
            _logger.info(f"Diff with expected XML (if any): {diff}")
            assert len(diff) == 0
