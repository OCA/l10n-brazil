# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import (
    FREQ_ENCERR,
    IND_NAT_TRIB,
    PLANO_CTA_REF,
    REG_TRIB_PRINC,
    TP_AMB,
)

from ..constants import (
    API_URL_PROD,
    API_URL_RESTRICTED,
    DEFAULT_API_PATH,
    DEFAULT_API_URL,
    DEFAULT_CONSULT_PATH,
    DEFAULT_VER_APLIC,
    TOKEN_URL_PROD,
)


class ResCompany(models.Model):
    _inherit = "res.company"

    dere_reg_trib_princ = fields.Selection(
        REG_TRIB_PRINC,
        string="DeRE main tax regime",
    )
    dere_reg_trib_secund = fields.Selection(
        [
            ("1", "Financial services"),
            ("2", "Health-care plans"),
            ("3", "Prize contests"),
        ],
        string="DeRE secondary tax regime",
    )
    dere_ind_nat_trib = fields.Selection(
        IND_NAT_TRIB,
        string="DeRE tax nature",
        default="0",
    )
    dere_plano_cta_ref = fields.Selection(
        PLANO_CTA_REF,
        string="DeRE referential chart",
    )
    dere_freq_encerr = fields.Selection(
        FREQ_ENCERR,
        string="DeRE closing frequency",
        default="M",
    )
    dere_activity_ids = fields.Many2many(
        comodel_name="l10n_br_dere.activity",
        string="DeRE activities",
    )
    dere_subject_d1106 = fields.Boolean(
        string="Subject to D-1106",
        help="Set if the taxpayer must send the technical-reserve investment event.",
    )
    dere_subject_d1121 = fields.Boolean(
        string="Subject to D-1121",
        help="Set if the taxpayer must send the deduction event when it applies.",
    )
    dere_tp_amb = fields.Selection(
        TP_AMB,
        string="DeRE environment",
        default="2",
    )
    dere_ver_aplic = fields.Char(
        string="DeRE application version",
        default=DEFAULT_VER_APLIC,
        size=20,
    )
    dere_token_url = fields.Char(
        string="Receita Integra token URL",
        default=TOKEN_URL_PROD,
    )
    dere_api_url = fields.Char(
        string="Receita Integra API URL",
        default=DEFAULT_API_URL,
    )
    dere_api_path = fields.Char(
        string="DeRE batch path",
        default=DEFAULT_API_PATH,
        help="Path appended to the API URL when posting a batch.",
    )
    dere_consult_path = fields.Char(
        string="DeRE consult path",
        default=DEFAULT_CONSULT_PATH,
        help="Path appended to the API URL when consulting a batch. Use {protocol}.",
    )
    dere_client_id = fields.Char(
        string="Receita Integra client id",
        groups="l10n_br_dere.group_manager",
    )
    dere_client_secret = fields.Char(
        string="Receita Integra client secret",
        groups="l10n_br_dere.group_manager",
    )
    dere_allow_force_delete = fields.Boolean(
        string="Allow deleting accepted DeRE records",
        groups="l10n_br_dere.group_manager",
        help="Testing only. Managers may delete sent or accepted declarations "
        "and table periods while the environment is restricted (tpAmb 2). "
        "This does not void receipts at the RFB.",
    )

    def _dere_can_force_delete(self):
        self.ensure_one()
        company = self.sudo()
        return bool(company.dere_allow_force_delete and company.dere_tp_amb == "2")

    def _dere_uses_restricted_gateway(self):
        self.ensure_one()
        base = (self.dere_api_url or DEFAULT_API_URL).rstrip("/")
        return base == API_URL_RESTRICTED.rstrip("/")

    def _dere_api_base_url(self):
        self.ensure_one()
        if self.dere_tp_amb == "1" and self._dere_uses_restricted_gateway():
            raise UserError(
                _(
                    "Production (tpAmb 1) cannot use the restricted Receita "
                    "Integra gateway. Set a production API URL when it is published."
                )
            )
        if self.dere_api_url:
            return self.dere_api_url.rstrip("/")
        if self.dere_tp_amb == "1":
            return API_URL_PROD
        return API_URL_RESTRICTED

    def _dere_batch_url(self):
        self.ensure_one()
        return self._dere_api_base_url() + (self.dere_api_path or DEFAULT_API_PATH)

    def _dere_cnpj(self):
        self.ensure_one()
        vat = ""
        partner = self.partner_id
        if partner and getattr(partner, "cnpj_cpf_stripped", None):
            vat = partner.cnpj_cpf_stripped or ""
        if not vat:
            vat = re.sub(r"[^0-9A-Z]", "", (self.vat or "").upper())
        return vat[:14]

    def _dere_cnpj_root(self):
        self.ensure_one()
        return self._dere_cnpj()[:8]
