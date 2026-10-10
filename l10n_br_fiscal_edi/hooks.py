# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    # The candidate SQL view is built conditionally from the optional
    # purchase/stock models. At module-graph time those models are not in
    # the registry yet, so the view was created empty: rebuild it with the
    # full registry.
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["l10n_br_fiscal.document.import.match.candidate"].refresh_view()
