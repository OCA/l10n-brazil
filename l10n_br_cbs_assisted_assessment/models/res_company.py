# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import secrets

from odoo import api, fields, models

from ..constants import (
    DEFAULT_API_URL,
    DEFAULT_TOKEN_URL,
    ENVIRONMENT_RESTRICTED,
    ENVIRONMENTS,
    WEBHOOK_ROUTE,
)


class ResCompany(models.Model):
    _inherit = "res.company"

    cbs_assessment_environment = fields.Selection(
        selection=ENVIRONMENTS,
        string="CBS Assessment Environment",
        default=ENVIRONMENT_RESTRICTED,
        required=True,
    )
    cbs_assessment_token_url = fields.Char(
        string="Token URL",
        default=DEFAULT_TOKEN_URL,
    )
    cbs_assessment_api_url = fields.Char(
        string="API URL",
        default=DEFAULT_API_URL,
    )
    cbs_assessment_client_id = fields.Char(string="Receita Integra Client Id")
    cbs_assessment_client_secret = fields.Char(string="Receita Integra Client Secret")
    cbs_assessment_webhook_token = fields.Char(
        string="Webhook Token",
        copy=False,
        help="Secret embedded in the callback URL. Rotating it invalidates the "
        "URL informed in requests that are still being processed.",
    )
    cbs_assessment_webhook_url = fields.Char(
        string="Callback URL",
        compute="_compute_cbs_assessment_webhook_url",
        help="URL to inform as urlRetorno. It must be reachable over HTTPS.",
    )

    @api.depends("cbs_assessment_webhook_token")
    def _compute_cbs_assessment_webhook_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        dbname = self.env.cr.dbname
        for company in self:
            company.cbs_assessment_webhook_url = (
                f"{(base_url or '').rstrip('/')}{WEBHOOK_ROUTE}/"
                f"{company.cbs_assessment_webhook_token}?db={dbname}"
                if company.cbs_assessment_webhook_token
                else False
            )

    def action_cbs_assessment_rotate_webhook_token(self):
        for company in self:
            company.cbs_assessment_webhook_token = secrets.token_urlsafe(32)
        return True

    def _cbs_assessment_webhook_url(self):
        """Return the callback URL, generating the token on first use."""
        self.ensure_one()
        if not self.cbs_assessment_webhook_token:
            self.action_cbs_assessment_rotate_webhook_token()
        return self.cbs_assessment_webhook_url
