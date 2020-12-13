# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from xmldiff import main
import os
import logging

from datetime import datetime
from odoo.tools import config
from ... import l10n_br_nfse_issnet

from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common \
    import TestFiscalDocumentNFSeCommon


_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSeIssnet(TestFiscalDocumentNFSeCommon):

    def setUp(self):
        super(TestFiscalDocumentNFSeIssnet, self).setUp()

        self.company.provedor_nfse = 'issnet'

    def test_nfse_issnet(self):
        """ Test NFS-e same state. """

        self.nfse_same_state._onchange_document_serie_id()
        self.nfse_same_state._onchange_fiscal_operation_id()
        self.nfse_same_state._onchange_company_id()
        self.nfse_same_state.rps_number = 50
        self.nfse_same_state.date = datetime.strptime(
            '2020-06-04T11:58:46', '%Y-%m-%dT%H:%M:%S')

        for line in self.nfse_same_state.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

        self.nfse_same_state.action_document_confirm()

        xml_path = os.path.join(
            l10n_br_nfse_issnet.__path__[0], 'tests', 'nfse',
            '001_50_nfse.xml')
        output = os.path.join(config['data_dir'], 'filestore', self.cr.dbname,
                              self.nfse_same_state.file_xml_id.store_fname)
        _logger.info("XML file saved at %s" % (output,))

        diff = main.diff_files(xml_path, output)
        _logger.info("Diff with expected XML (if any): %s" % (diff,))

        assert len(diff) == 0
