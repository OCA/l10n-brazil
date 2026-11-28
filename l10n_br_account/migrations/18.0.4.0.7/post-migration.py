# Copyright (C) 2026  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.flush_all()
    for model_name in ("l10n_br_fiscal.document", "l10n_br_fiscal.document.line"):
        model = env[model_name]
        for proxy, shadowed in model._proxy_shadowed_columns.items():
            if not (
                column_exists(cr, model._table, proxy)
                and column_exists(cr, model._table, shadowed)
            ):
                continue
            count = model._fill_proxy_column(proxy)
            _logger.info(
                "%s.%s: %s rows filled from %s", model._table, proxy, count, shadowed
            )
    env.invalidate_all()
