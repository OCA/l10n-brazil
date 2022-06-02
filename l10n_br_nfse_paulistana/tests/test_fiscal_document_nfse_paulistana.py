# Copyright 2020 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from datetime import datetime

from xmldiff import main

from odoo.tools import config

from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

from ... import l10n_br_nfse_paulistana

_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSePaulistana(TestFiscalDocumentNFSeCommon):
    def setUp(self):
        super(TestFiscalDocumentNFSePaulistana, self).setUp()
        self.company.provedor_nfse = "paulistana"

    def test_nfse_paulistana(self):
        """Test NFS-e same state."""

        xml_path = os.path.join(
            l10n_br_nfse_paulistana.__path__[0], "tests", "nfse", "paulistana.xml"
        )

        self.nfse_same_state._onchange_document_serie_id()
        self.nfse_same_state._onchange_fiscal_operation_id()
        self.nfse_same_state._onchange_company_id()
        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        for line in self.nfse_same_state.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

        self.nfse_same_state.action_document_confirm()

        self.nfse_same_state.document_date = datetime.strptime(
            "2020-06-04T11:58:46", "%Y-%m-%dT%H:%M:%S"
        )
        self.nfse_same_state.date_in_out = datetime.strptime(
            "2020-06-04T11:58:46", "%Y-%m-%dT%H:%M:%S"
        )

        self.nfse_same_state.with_context(lang="pt_BR")._document_export()

        output = os.path.join(
            config["data_dir"],
            "filestore",
            self.cr.dbname,
            self.nfse_same_state.send_file_id.store_fname,
        )
        _logger.info("XML file saved at %s" % (output,))

        diff = main.diff_files(xml_path, output)
        _logger.info("Diff with expected XML (if any): %s" % (diff,))

        assert len(diff) == 0
