# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import logging

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentTokenCielo(models.Model):
    _inherit = "payment.token"

    cielo_token = fields.Char(string="Cielo Token", groups="base.group_user")
    card_brand = fields.Char(string="Card Brand")

    def _cielo_tokenize(self, values):
        """Tokeniza um cartão no endpoint Cielo.

        Espera `values` com chaves: cc_number, cc_holder_name, cc_expiry, cc_brand, partner_id
        Retorna o JSON do gateway ou lança exceção em caso de erro.
        """
        provider = self.env.ref("payment_cielo.payment_provider_cielo")
        api_host = provider._get_cielo_api_url()
        api_url_create_card = f"https://{api_host}/1/card"

        partner = self.env["res.partner"].browse(values.get("partner_id"))

        # formato esperado: MMYY ou MM/YY -> é transformado para MM/YYYY
        expiry = (values.get("cc_expiry") or "").replace(" ", "")
        if "/" in expiry:
            mm, yy = (p.strip() for p in expiry.split("/"))
        else:
            mm, yy = expiry[:2], expiry[-2:]
        try:
            year4 = int(yy)
            if year4 < 100:
                year4 = (datetime.datetime.now().year // 100) * 100 + int(yy)
        except Exception:
            year4 = datetime.datetime.now().year
        cielo_expiry = f"{mm}/{year4}"

        brand = (values.get("cc_brand") or "").strip()
        if brand.lower() == "mastercard":
            brand = "Master"

        payload = {
            "CustomerName": partner.name or "",
            "CardNumber": (values.get("cc_number") or "").replace(" ", ""),
            "Holder": values.get("cc_holder_name") or "",
            "ExpirationDate": cielo_expiry,
            "Brand": brand,
        }

        _logger.info(
            "Cielo tokenize: POST %s -> payload keys: %s",
            api_url_create_card,
            list(payload.keys()),
        )
        try:
            r = requests.post(
                api_url_create_card,
                json=payload,
                headers=provider._get_cielo_api_headers(),
                timeout=30,
            )
            r.raise_for_status()
            resp = r.json()
        except requests.RequestException:
            _logger.exception("Cielo tokenize request failed")
            raise
        except ValueError:
            _logger.exception("Cielo returned invalid JSON for tokenize")
            raise

        return resp

    @api.model
    def cielo_create(self, values):
        """Cria um registro temporário de token a partir dos dados enviados pelo formulário S2S.

        Não salva PAN/CVC no banco, apenas armazena o token retornado pela Cielo.
        """
        token_response = self._cielo_tokenize(values)
        card_token = (
            token_response.get("CardToken")
            or token_response.get("cardToken")
            or token_response.get("id")
        )
        if not card_token:
            _logger.error("Cielo: tokenization failed, response: %s", token_response)
            return False

        partner = self.env["res.partner"].browse(values.get("partner_id"))
        short_name = f"XXXX-XXXX-XXXX-{(values.get('cc_number') or '')[-4:]} - {partner.name or ''}"

        res = {
            "provider_ref": partner.id,
            "name": short_name,
            "cielo_token": card_token,
            "card_brand": (values.get("cc_brand") or "").lower(),
        }
        return res
