# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import pprint

import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentController(http.Controller):

    _accept_url = "/payment/pay24pix/feedback"

    @http.route(
        [
            "/payment/pay24pix/feedback",
        ],
        type="http",
        auth="public",
        csrf=False,
    )
    def transfer_form_feedback(self, **post):
        _logger.info(
            "Beginning form_feedback with post data %s", pprint.pformat(post)
        )  # debug
        request.env["payment.transaction"].sudo().form_feedback(post, "pay24pix")
        return werkzeug.utils.redirect("/payment/process")

    @http.route(
        "/payment/pay24pix/webhook/<string:tx_reference>",
        type="json",
        auth="public",
        csrf=False,
    )
    def pay24pix_webhook(self, tx_reference):
        request.env["payment.acquirer"].sudo()._handle_pay24pix_webhook(
            tx_reference, request.jsonrequest
        )
        return "OK"
