import os
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub
from odoo.tests.common import TransactionCase
from odoo.addons import l10n_br_nfe_spec


class NFeImportTest(TransactionCase):
    def test_import_all_nfes(self):
        path = os.path.join(l10n_br_nfe_spec.__path__[0],
                            'tests', 'nfe', 'v4_00', 'leiauteNFe')
        for filename in os.listdir(path):
            print(filename, dir(self.env["nfe.40.infnfe"]))
            obj = nfe_sub.parse('%s/%s' % (path, filename,))
            print(obj.infNFe)
            nfe = self.env["nfe.40.infnfe"].build(obj.infNFe)
            print(nfe.nfe40_emit.nfe40_CNPJ)
