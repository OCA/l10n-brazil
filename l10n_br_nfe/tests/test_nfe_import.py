import logging
import os
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub
from odoo.tests.common import TransactionCase
from odoo.addons import l10n_br_nfe

_logger = logging.getLogger(__name__)


class NFeImportTest(TransactionCase):
    def test_import_all_nfes(self):
        path = os.path.join(l10n_br_nfe.__path__[0],
                            'tests', 'nfe', 'v4_00', 'leiauteNFe')
        for filename in os.listdir(path):
            _logger.info(filename, dir(self.env["nfe.40.infnfe"]))
            obj = nfe_sub.parse('%s/%s' % (path, filename,))
            _logger.info(obj.infNFe)
            nfe = self.env["nfe.40.infnfe"].build(obj.infNFe)
            _logger.info(nfe.nfe40_emit.nfe40_CNPJ)
