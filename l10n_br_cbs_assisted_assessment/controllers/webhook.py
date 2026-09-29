# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging

from odoo import http
from odoo.http import request

from ..constants import WEBHOOK_ROUTE

_logger = logging.getLogger(__name__)


class CbsAssessmentWebhook(http.Controller):
    """Callback endpoint informed to the tax administration as urlRetorno.

    The gateway validates the URL with a HEAD request before accepting the
    assessment request, and later posts the signed download URL to it. The route
    is public because the caller has no Odoo session; the secret in the path is
    what authorises it.
    """

    @http.route(
        f"{WEBHOOK_ROUTE}/<string:token>",
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def callback(self, token, **kwargs):
        company = self._company_from_token(token)
        if not company:
            _logger.warning("CBS assessment callback reached with an unknown token")
            return self._answer({"status": "unknown"}, 404)
        if http.request.httprequest.method != "POST":
            # Answers the HEAD validation performed when the request is opened.
            return self._answer({"status": "ready"}, 200)
        try:
            payload = json.loads(request.httprequest.get_data(as_text=True) or "{}")
        except ValueError:
            return self._answer({"status": "invalid payload"}, 400)
        ticket = payload.get("tiqueteSolicitacao")
        assessment_request = self._request_from_ticket(company, ticket)
        if not assessment_request:
            _logger.warning(
                "CBS assessment callback for unknown ticket on company %s",
                company.id,
            )
            return self._answer({"status": "unknown ticket"}, 404)
        assessment_request.register_callback(payload)
        return self._answer({"status": "accepted"}, 200)

    def _company_from_token(self, token):
        if not token:
            return False
        return (
            request.env["res.company"]
            .sudo()
            .search(
                [
                    ("cbs_assessment_webhook_token", "!=", False),
                    ("cbs_assessment_webhook_token", "=", token),
                ],
                limit=1,
            )
        )

    def _request_from_ticket(self, company, ticket):
        if not ticket:
            return False
        return (
            request.env["l10n_br_assessment.request"]
            .sudo()
            .search(
                [
                    ("company_id", "=", company.id),
                    ("ticket", "=", ticket),
                ],
                limit=1,
            )
        )

    def _answer(self, payload, status):
        return request.make_json_response(payload, status=status)
