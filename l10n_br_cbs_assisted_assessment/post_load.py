# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import http

from .constants import WEBHOOK_ROUTE

_logger = logging.getLogger(__name__)


def post_load():
    """Resolve the database from the ``db`` query parameter on the webhook.

    The tax administration calls the callback without an Odoo session. When the
    server exposes more than one database, a sessionless request cannot tell
    which one to open and the route answers 404 before the controller runs.
    Same approach used by OCA queue_job for ``/queue_job/runjob``.
    """
    _logger.info(
        "Apply Request._get_session_and_dbname monkey patch to capture db"
        " on the CBS assessment webhook"
    )
    _get_session_and_dbname_orig = http.Request._get_session_and_dbname

    def _get_session_and_dbname(self):
        session, dbname = _get_session_and_dbname_orig(self)
        path = self.httprequest.path or ""
        candidate = self.httprequest.args.get("db")
        if not dbname and candidate and path.startswith(f"{WEBHOOK_ROUTE}/"):
            host = self.httprequest.environ.get("HTTP_HOST")
            if candidate in http.db_list(force=True, host=host):
                dbname = candidate
                session.db = candidate
        return session, dbname

    http.Request._get_session_and_dbname = _get_session_and_dbname
