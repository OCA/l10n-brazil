# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentProviderCielo(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("cielo", "Cielo")], ondelete={"cielo": "set default"}
    )
    cielo_merchant_key = fields.Char(
        required_if_provider="cielo", groups="base.group_user"
    )
    cielo_merchant_id = fields.Char(
        string="Cielo Merchant Id",
        required_if_provider="cielo",
        groups="base.group_user",
    )
    cielo_image_url = fields.Char("Checkout Image URL", groups="base.group_user")

    def cielo_s2s_form_validate(self, data):
        self.ensure_one()
        _logger.debug("Validating Cielo S2S form data: keys=%s", list(data.keys()))
        required = [
            "cc_number",
            "cvc",
            "cc_holder_name",
            "cc_expiry",
            "cc_brand",
            "provider_id",
            "partner_id",
        ]
        missing = [f for f in required if not data.get(f)]
        if missing:
            _logger.warning("Cielo S2S missing fields: %s", missing)
            return False
        return True

    @api.model
    def cielo_s2s_form_process(self, data):
        """Processa os dados do formulário S2S e cria um payment.token com o token recebido.

        Espera `data` contendo os dados do cartão ou um token já gerado.
        """
        Token = self.env["payment.token"].sudo()
        vals = {
            "provider_id": int(data.get("provider_id"))
            if data.get("provider_id")
            else None,
            "partner_id": int(data.get("partner_id"))
            if data.get("partner_id")
            else None,
        }
        if data.get("cielo_token"):
            vals["cielo_token"] = data.get("cielo_token")
            return Token.create(vals)

        token = None
        if data.get("provider_id"):
            try:
                token = (
                    self.env["payment.provider"]
                    .browse(int(data.get("provider_id")))
                    .s2s_process(data)
                )
            except Exception:
                _logger.exception("Error calling provider.s2s_process for tokenization")
                raise
        return token

    def _get_cielo_api_url(self):
        if self.state == "test":
            return "apisandbox.cieloecommerce.cielo.com.br"
        return "api.cieloecommerce.cielo.com.br"

    def _get_cielo_api_headers(self):
        if self.state == "test":
            return {
                "MerchantId": "be87a4be-a40d-4a2d-b2c8-b8b6cc19cddd",
                "MerchantKey": "POHAWRXFBSIXTMTFVBCYSKNWZBMOATDNYUQDGBUE",
                "Content-Type": "application/json",
            }
        if not self.cielo_merchant_id or not self.cielo_merchant_key:
            raise ValueError(
                "Cielo merchant credentials are required in production state"
            )
        return {
            "MerchantId": self.cielo_merchant_id,
            "MerchantKey": self.cielo_merchant_key,
            "Content-Type": "application/json",
        }

    def _get_feature_support(self):
        res = super()._get_feature_support()
        if "tokenize" in res:
            res["tokenize"].append("cielo")
        if "authorize" in res:
            res["authorize"].append("cielo")
        return res
