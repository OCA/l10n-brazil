# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hmac
import logging

from brbank.erros import ErroBrbank

from odoo import fields, http
from odoo.exceptions import UserError
from odoo.http import request

from ..models.connection import (
    ADMIN_GROUP,
    OAUTH_CALLBACK_ROUTE,
    OAUTH_START_ROUTE,
    WEBHOOK_ROUTE,
)

_logger = logging.getLogger(__name__)

MODEL = "l10n_br_bank_connection.connection"


def token_matches(expected, token):
    """Compare a webhook token in constant time; empty never matches."""
    return bool(expected) and hmac.compare_digest(
        (expected or "").encode(), (token or "").encode()
    )


def dispatch_webhook(connection):
    """Hand the request in progress to the domains of the connection."""
    try:
        counts = connection._l10n_br_bank_handle_webhook(
            request.httprequest.get_data(), dict(request.httprequest.headers)
        )
    except (ErroBrbank, UserError, ValueError) as error:
        _logger.info(
            "bank connection %s: webhook payload refused (%s)",
            connection.id,
            type(error).__name__,
        )
        return request.make_response("", status=400)
    return request.make_json_response(counts or {})


class BankConnectionController(http.Controller):
    @http.route(
        WEBHOOK_ROUTE + "/<int:connection_id>/<string:token>",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def webhook(self, connection_id, token, **kwargs):
        """Receive a bank notification: validate, hand to the domains, answer."""
        connection = request.env[MODEL].sudo().browse(connection_id).exists()
        expected = connection.webhook_token if connection.active else ""
        if not token_matches(expected, token):
            return request.make_response("", status=404)
        return dispatch_webhook(connection)

    @http.route(
        OAUTH_START_ROUTE + "/<int:connection_id>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def oauth_start(self, connection_id, **kwargs):
        """Send the administrator to the consent page of the bank."""
        user = request.env.user
        if not user.has_group(ADMIN_GROUP):
            return request.make_response("", status=403)
        connection = request.env[MODEL].browse(connection_id).exists()
        if not connection:
            return request.not_found()
        try:
            url = connection._l10n_br_bank_oauth_start()
        except UserError as error:
            return self._back(connection, str(error))
        return request.redirect(url, local=False)

    @http.route(
        OAUTH_CALLBACK_ROUTE,
        type="http",
        auth="user",
        methods=["GET"],
    )
    def oauth_callback(self, code=None, state=None, error=None, **kwargs):
        """Finish the consent: check `state`, exchange the code, save the token."""
        user = request.env.user
        if not user.has_group(ADMIN_GROUP):
            return request.make_response("", status=403)
        connection = request.env[MODEL].browse()
        if state:
            connection = (
                request.env[MODEL].sudo().search([("oauth_state", "=", state)], limit=1)
            )
        expected = connection.oauth_state if connection else ""
        if (
            not token_matches(expected, state)
            or not connection.oauth_expires
            or connection.oauth_expires < fields.Datetime.now()
        ):
            return request.make_response("The consent request expired.", status=400)
        if error or not code:
            connection.write(
                {
                    "oauth_state": False,
                    "oauth_verifier": False,
                    "oauth_expires": False,
                    "last_error": "consent refused at the bank",
                }
            )
            return self._back(connection)
        message = None
        try:
            connection._l10n_br_bank_oauth_finish(code)
        except UserError as exc:
            message = str(exc)
            connection.write({"last_error": message[:500]})
        return self._back(connection, message)

    @staticmethod
    def _back(connection, message=None):
        if message:
            _logger.info("bank connection %s: consent not completed", connection.id)
        return request.redirect(f"/web#id={connection.id}&model={MODEL}&view_type=form")
