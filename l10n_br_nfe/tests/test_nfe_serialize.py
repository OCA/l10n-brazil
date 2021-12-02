# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from datetime import datetime

from xmldiff import main

from odoo.tests.common import TransactionCase
from odoo.tools import config

from odoo.addons import l10n_br_nfe
from odoo.addons.spec_driven_model import hooks

_logger = logging.getLogger(__name__)


class TestNFeExport(TransactionCase):
    def setUp(self):
        super(TestNFeExport, self).setUp()
        hooks.register_hook(
            self.env,
            "l10n_br_nfe",
            "odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe",
        )
        self.nfe_list = []

    def prepare_test_nfe(self, nfe):
        """
        Performs actions necessary to prepare an NFe of the demo data to
        perform the tests
        """
        if nfe.state != "em_digitacao":  # 2nd test run
            nfe.action_document_back2draft()

        for line in nfe.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()

        nfe._compute_amount()

    def test_serialize_xml(self):
        for nfe in self.nfe_list:
            nfe_id = nfe["record_id"]

            self.prepare_test_nfe(nfe_id)

            xml_path = os.path.join(
                l10n_br_nfe.__path__[0],
                "tests",
                "nfe",
                "v4_00",
                "leiauteNFe",
                nfe["xml_file"],
            )
            financial_vals = nfe_id._prepare_amount_financial(
                "0", "01", nfe_id.amount_financial_total
            )
            nfe_id.nfe40_detPag = [(5, 0, 0), (0, 0, financial_vals)]
            nfe_id.action_document_confirm()
            nfe_id.document_date = datetime.strptime(
                "2020-01-01T11:00:00", "%Y-%m-%dT%H:%M:%S"
            )
            nfe_id.date_in_out = datetime.strptime(
                "2020-01-01T11:00:00", "%Y-%m-%dT%H:%M:%S"
            )
            nfe_id.nfe40_cNF = "06277716"
            nfe_id.with_context(lang="pt_BR")._document_export()
            output = os.path.join(
                config["data_dir"],
                "filestore",
                self.cr.dbname,
                nfe_id.send_file_id.store_fname,
            )
            _logger.info("XML file saved at %s" % (output,))
            nfe_id.company_id.country_id.name = "Brazil"  # clean mess
            diff = main.diff_files(output, xml_path)
            _logger.info("Diff with expected XML (if any): %s" % (diff,))
            assert len(diff) == 0
