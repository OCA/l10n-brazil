# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from datetime import datetime

from xmldiff import main

from odoo.tools import config

from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

from ... import l10n_br_nfse_nacional

_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSeNacional(TestFiscalDocumentNFSeCommon):
    def setUp(self):
        super(TestFiscalDocumentNFSeNacional, self).setUp()
        self.company.provedor_nfse = "nacional"

    def test_nfse_nacional(self):
        """Test NFS-e same state."""

        xml_path = os.path.join(
            l10n_br_nfse_nacional.__path__[0], "tests", "nfse", "nacional.xml"
        )

        self.nfse_same_state._onchange_document_serie_id()
        self.nfse_same_state._onchange_fiscal_operation_id()
        self.nfse_same_state._onchange_company_id()
        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        for line in self.nfse_same_state.fiscal_line_ids:
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

        # TODO mock and test
        # self.nfse_same_state.action_document_send()
