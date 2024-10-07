# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint

import werkzeug

from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentProcessing

_logger = logging.getLogger(__name__)


class CieloController(http.Controller):
    @http.route(
        ["/payment/cielo/s2s/create_json_3ds"],
        type="json",
        auth="public",
        csrf=False,
        website=True,
    )
    def cielo_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        if not kwargs.get("partner_id"):
            kwargs["partner_id"] = request.env.user.partner_id.id
        token = (
            request.env["payment.acquirer"]
            .browse(int(kwargs.get("acquirer_id")))
            .s2s_process(kwargs)
        )

        if not token:
            res = {
                "result": False,
            }
            return res

        res = {
            "result": True,
            "id": token.id,
            "short_name": token.short_name,
            "3d_secure": False,
            "verified": False,
        }

        if verify_validity is not False:
            token.validate()
            res["verified"] = token.verified

        return res

    @http.route(["/payment/cielo/create_charge"], type="json", auth="public")
    def cielo_create_charge(self, **post):
        """Create a payment transaction.
        Expect the result from the user input from checkout.js popup."""
        TX = request.env["payment.transaction"]
        tx = None
        if post.get("tx_ref"):
            tx = TX.sudo().search([("reference", "=", post["tx_ref"])])
        if not tx:
            tx_id = (
                post.get("tx_id")
                or request.session.get("sale_transaction_id")
                or request.session.get("website_payment_tx_id")
            )
            tx = TX.sudo().browse(int(tx_id))
        if not tx:
            raise werkzeug.exceptions.NotFound()

        cielo_token = post["token"]
        response = None
        if tx.type == "form_save" and tx.partner_id:
            payment_token_id = (
                request.env["payment.token"]
                .sudo()
                .create(
                    {
                        "acquirer_id": tx.acquirer_id.id,
                        "partner_id": tx.partner_id.id,
                        "cielo_token": cielo_token,
                    }
                )
            )
            tx.payment_token_id = payment_token_id
            response = tx._create_cielo_charge(
                acquirer_ref=payment_token_id.acquirer_ref, email=cielo_token["email"]
            )
        else:
            response = tx._create_cielo_charge(
                tokenid=cielo_token["id"], email=cielo_token["email"]
            )
        _logger.info(
            "Cielo: entering form_feedback with post data %s", pprint.pformat(response)
        )
        if response:
            request.env["payment.transaction"].sudo().with_context(
                lang=None
            ).form_feedback(response, "cielo")
        # Add the payment transaction into the session to let the page
        # /payment/process handle it.
        PaymentProcessing.add_payment_transaction(tx)
        return "/payment/process"
