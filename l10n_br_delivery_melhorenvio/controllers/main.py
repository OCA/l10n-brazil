# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request


class MelhorEnvioOAuth(http.Controller):
    @http.route("/melhorenvio/oauth/callback", type="http", auth="user")
    def melhorenvio_oauth_callback(self, code=None, state=None, **kwargs):
        """Melhor Envio sends the browser back here after the authorization."""
        env = request.env
        if not env.user.has_group("base.group_system"):
            raise AccessError(env._("Only administrators can authorize Melhor Envio."))
        account = (
            env["melhorenvio.account"]
            .sudo()
            .with_context(active_test=False)
            .search([("oauth_state", "=", state or "-")], limit=1)
        )
        if not account:
            raise UserError(env._("Unknown Melhor Envio authorization request."))
        if not code:
            raise UserError(
                env._(
                    "Melhor Envio did not authorize the application: %(error)s",
                    error=kwargs.get("error_description") or kwargs.get("error"),
                )
            )
        account._exchange_token({"grant_type": "authorization_code", "code": code})
        return request.redirect(
            f"/odoo/action-l10n_br_delivery_melhorenvio."
            f"melhorenvio_account_action/{account.id}"
        )
