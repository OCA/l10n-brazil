# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import fields, models

from ..constants import SERPRO_ENVIRONMENT

# Ask for a new token a minute before the old one dies, so a long request does
# not start with a token that expires halfway.
TOKEN_SAFETY_MARGIN = 60


class ResCompany(models.Model):
    """Credentials and addressing of the Integra Contador.

    The key, the secret and the token are only readable by the system group:
    they are the credential of the company at the tax authority, not
    configuration an accountant needs to see.
    """

    _inherit = "res.company"

    serpro_environment = fields.Selection(
        selection=SERPRO_ENVIRONMENT,
        string="Integra Contador environment",
        default="trial",
    )
    serpro_consumer_key = fields.Char(
        string="Integra Contador consumer key",
        groups="base.group_system",
    )
    serpro_consumer_secret = fields.Char(
        string="Integra Contador consumer secret",
        groups="base.group_system",
    )
    serpro_access_token = fields.Char(
        string="Integra Contador token",
        groups="base.group_system",
        copy=False,
        help="Kept only to avoid asking for a new token on every call.",
    )
    serpro_token_expiration = fields.Datetime(
        string="Token expiration",
        groups="base.group_system",
        copy=False,
    )
    serpro_jwt_token = fields.Char(
        string="Attorney token",
        groups="base.group_system",
        copy=False,
        help="The jwt_token the Authenticate Attorney service answers, used "
        "when an accounting firm files for its client.",
    )
    serpro_contractor_cnpj = fields.Char(
        size=14,
        string="Contractor CNPJ",
        help="The CNPJ that signed the Integra Contador contract. Leave it "
        "empty to use the CNPJ of this company.",
    )
    serpro_author_cnpj = fields.Char(
        size=14,
        string="Request author CNPJ",
        help="The CNPJ asking for the data, the accounting firm when it files "
        "for a client. Leave it empty to use the contractor.",
    )
    serpro_warn_cost = fields.Boolean(
        string="Warn before a billed call",
        default=True,
        help="The Integra Contador is billed per request. With this on, every "
        "billed call asks for confirmation first.",
    )

    def _serpro_digits(self, value):
        return "".join(filter(str.isdigit, value or ""))

    def _serpro_contractor_cnpj(self):
        self.ensure_one()
        return self._serpro_digits(self.serpro_contractor_cnpj or self.cnpj_cpf)

    def _serpro_author_cnpj(self):
        self.ensure_one()
        return self._serpro_digits(
            self.serpro_author_cnpj or self.serpro_contractor_cnpj or self.cnpj_cpf
        )

    def _serpro_token_expired(self):
        self.ensure_one()
        if not self.serpro_token_expiration:
            return True
        return self.serpro_token_expiration <= fields.Datetime.now()

    def _store_serpro_token(self, token, expires_in):
        self.ensure_one()
        values = {"serpro_access_token": token}
        if expires_in:
            values["serpro_token_expiration"] = fields.Datetime.now() + timedelta(
                seconds=max(int(expires_in) - TOKEN_SAFETY_MARGIN, 0)
            )
        self.sudo().write(values)
