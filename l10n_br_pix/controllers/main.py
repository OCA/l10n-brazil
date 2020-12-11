# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PixController(http.Controller):

    @http.route(
        "/pix/webhook/sandbox", methods=["POST"], auth="public", type="http", csrf=False)
    def pix_webhook(self):
        _logger.debug("/pix/webhook/sandbox")
        request.env["l10n_br_pix.cob"].sudo().sandbox()
