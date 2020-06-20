# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from . import models
from . import tests

from odoo.addons import account
from odoo import api, SUPERUSER_ID

# Install Simple Chart of Account Template for Brazilian Companies
_auto_install_l10n_original = account._auto_install_l10n


def _auto_install_l10n_br_generic_module(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    country_code = env.user.company_id.country_id.code
    if country_code and country_code.upper() == "BR":
        if hasattr(env.user.company_id, 'tax_framework') and \
                env.user.company_id.tax_framework == '3':
            module_name_domain = [("name", "=", "l10n_br_coa_generic")]
        else:
            module_name_domain = [("name", "=", "l10n_br_coa_simple")]
        module_ids = env["ir.module.module"].search(
            module_name_domain + [("state", "=", "uninstalled")]
        )
        module_ids.sudo().button_install()
    else:
        _auto_install_l10n_original(cr, registry)


account._auto_install_l10n = _auto_install_l10n_br_generic_module
