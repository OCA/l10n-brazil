# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os

from xmldiff import main

from odoo.tests.common import TransactionCase
from odoo.tools import config

from odoo.addons import l10n_br_nfe

_logger = logging.getLogger(__name__)


class TestNFeExport(TransactionCase):
    def setUp(self, nfe_list):
        super().setUp()
        self.env["spec.mixin.nfe"]._register_hook()
        self.nfe_list = nfe_list
        for nfe_data in self.nfe_list:
            nfe = self.env.ref(nfe_data["record_ref"])
            nfe_data["nfe"] = nfe
            self.prepare_test_nfe(nfe)

    def prepare_test_nfe(self, nfe):
        """
        Performs actions necessary to prepare an NFe of the demo data to
        perform the tests
        """
        if nfe.state != "em_digitacao":  # 2nd test run
            nfe.action_document_back2draft()

        for line in nfe.fiscal_line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()

        nfe._compute_amount()
        nfe.nfe40_detPag = [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "01",
                    "nfe40_vPag": nfe.amount_financial_total,
                },
            ),
        ]
        nfe.action_document_confirm()
        nfe.nfe40_cNF = "06277716"
        nfe.company_id.country_id.name = "Brasil"
        nfe._document_export()

    def serialize_xml(self, nfe_data):
        nfe = nfe_data["nfe"]
        xml_path = os.path.join(
            l10n_br_nfe.__path__[0],
            "tests",
            "nfe",
            "v4_00",
            "leiauteNFe",
            nfe_data["xml_file"],
        )
        output = os.path.join(
            config["data_dir"],
            "filestore",
            self.cr.dbname,
            nfe.send_file_id.store_fname,
        )
        _logger.info(f"XML file saved at {output}")
        diff = main.diff_files(output, xml_path)
        return diff
