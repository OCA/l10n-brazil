# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from xmldiff import main
from xmldiff import formatting

from odoo.tools import config
import os
import logging

from odoo.tests.common import TransactionCase
from odoo.addons import l10n_br_nfe
from odoo.addons.l10n_br_fiscal.constants.fiscal import PROCESSADOR_OCA
from odoo.addons.spec_driven_model import hooks

_logger = logging.getLogger(__name__)


class TestNFeExport(TransactionCase):
    def setUp(self):
        super(TestNFeExport, self).setUp()
        hooks.register_hook(self.env, 'l10n_br_nfe',
                            'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe')
        self.nfe = self.env.ref('l10n_br_nfe.demo_nfe_same_state')
        self.nfe.write(
            {'document_type_id': self.env.ref('l10n_br_fiscal.document_55').id,
             'company_id': self.env.ref('l10n_br_base.empresa_lucro_presumido').id,
             'company_number': 3,
             'processador_edoc': PROCESSADOR_OCA,
             })
        self.nfe.company_id.processador_edoc = PROCESSADOR_OCA
        if self.nfe.state != 'em_digitacao':  # 2nd test run
            self.nfe.action_document_back2draft()

        for line in self.nfe.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()

        self.nfe.company_id.street_number = '3'

    def test_serialize_xml(self):
        xml_path = os.path.join(
            l10n_br_nfe.__path__[0], 'tests', 'nfe', 'v4_00', 'leiauteNFe',
            'NFe35200697231608000169550010000000111855451724-nf-e.xml')
        self.nfe.date = datetime.strptime(
            '2020-06-04T11:58:46', '%Y-%m-%dT%H:%M:%S')
        self.nfe.date_in_out = datetime.strptime(
            '2020-06-04T11:58:46', '%Y-%m-%dT%H:%M:%S')
        self.nfe.nfe40_cNF = '06277716'
        self.nfe.nfe40_serie = '1'
        financial_vals = self.nfe._prepare_amount_financial(
            '0', '01', self.nfe.amount_financial
        )
        self.nfe.nfe40_detPag = [(5, 0, 0), (0, 0, financial_vals)]
        self.nfe.with_context(lang='pt_BR').action_document_confirm()
        output = os.path.join(config['data_dir'], 'filestore',
                              self.cr.dbname, self.nfe.file_xml_id.store_fname)
        _logger.info("XML file saved at %s" % (output,))
        self.nfe.company_id.country_id.name = 'Brazil'  # clean mess
        diff = main.diff_files(
            xml_path, output, formatter=formatting.DiffFormatter(pretty_print=True)
        )
        _logger.info("Diff with expected XML (if any): \n%s" % (diff,))
        assert len(diff) == 0
