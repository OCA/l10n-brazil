# Copyright (C) 2019 - Raphael Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import os
from odoo import api, SUPERUSER_ID
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub
from odoo.addons import l10n_br_nfe
from odoo.addons.spec_driven_model import hooks


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    hooks.register_hook(env, 'l10n_br_nfe',
                        'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe')

    hooks.post_init_hook(cr, registry, 'l10n_br_nfe',
                         'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe')
    cr.execute("select demo from ir_module_module where name='l10n_br_nfe';")
    is_demo = cr.fetchone()[0]
    if is_demo:
        path = os.path.join(l10n_br_nfe.__path__[0],
                            'tests', 'nfe', 'v4_00', 'leiauteNFe')
        filename = os.listdir(path)[0]
        obj = nfe_sub.parse('%s/%s' % (path, filename,))
        # print(filename, obj.infNFe)
        env["nfe.40.infnfe"].build(obj.infNFe, {})
