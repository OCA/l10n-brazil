# Copyright (C) 2019 - Raphael Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import os
from odoo import api, SUPERUSER_ID
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub
from odoo.addons import l10n_br_nfe_spec


def post_init_hook(cr, registry):
    cr.execute("select demo from ir_module_module where name='l10n_br_nfe';")
    is_demo = cr.fetchone()[0]
    if is_demo:
       env = api.Environment(cr, SUPERUSER_ID, {})
#       fiscal_doc_id = env.ref(
#           'l10n_br_fiscal.l10n_br_document_serie_1_product').id
       path = os.path.join(l10n_br_nfe_spec.__path__[0],
                            'tests', 'nfe', 'v4_00', 'leiauteNFe')
       for filename in os.listdir(path)[1:50]:
            obj = nfe_sub.parse('%s/%s' % (path, filename,))
            # print(filename, obj.infNFe)
            env["account.invoice"].build(obj.infNFe, {})#'document_serie_id':
#                                                      fiscal_doc_id})
