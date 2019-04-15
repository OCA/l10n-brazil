# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.addons import account
from odoo import api, SUPERUSER_ID

from . import models
from . import tools
from . import tests


_auto_install_l10n_original = account._auto_install_l10n


def _auto_install_l10n(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    country_code = env.user.company_id.country_id.code
    if country_code and country_code == 'BR':
        module_ids = env['ir.module.module'].search(
            [('name', 'in', ('l10n_br_generic',)),
             ('state', '=', 'uninstalled')])
        module_ids.sudo().button_install()
    else:
        _auto_install_l10n_original(cr, registry)

account._auto_install_l10n = _auto_install_l10n
