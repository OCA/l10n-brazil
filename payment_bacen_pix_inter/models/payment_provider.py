import json

import requests
from werkzeug.urls import url_join

from odoo import api, fields, models
from odoo.exceptions import ValidationError

INTERPIX_PROVIDER = "inter_pix"

INTERPIX_SANDBOX_URL = "https://cdpj-sandbox.partners.uatinter.co/"
INTERPIX_PROD_URL = "https://cdpj.partners.bancointer.com.br/"

INTERPIX = {
    "enabled": INTERPIX_PROD_URL,
    "test": INTERPIX_SANDBOX_URL,
}


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[(INTERPIX_PROVIDER, "Banco Inter Pix")],
        ondelete={INTERPIX_PROVIDER: "set default"},
    )

    @api.constrains("code")
    def _check_interpix_configuration(self):
        """Valida configurações obrigatórias para o provider Inter Pix"""
        for provider in self:
            if provider.code == INTERPIX_PROVIDER and provider.state != "disabled":
                required_fields = [
                    "bacen_pix_key",
                    "bacenpix_client_id",
                    "bacenpix_client_secret",
                ]
                missing_fields = [
                    provider._fields[field].string
                    for field in required_fields
                    if not getattr(provider, field)
                ]
                if missing_fields:
                    raise ValidationError(
                        f"Configuração incompleta do Banco Inter Pix. "
                        f"Campos obrigatórios: {', '.join(missing_fields)}"
                    )

    def _interpix_header(self):
        """Retorna headers para requisição ao Inter"""
        return {
            "Authorization": f"Bearer {self.inter_pix_client_secret}",
            "Content-Type": "application/json",
        }

    def _interpix_new_transaction(self, tx_id, payload):
        """Cria cobrança PIX no Inter"""
        params = {"txid": tx_id}
        response = requests.request(
            "PUT",
            url_join(INTERPIX[self.state], "pix/v1/cob/"),
            params=params,
            headers=self._interpix_header(),
            data=json.dumps(payload),
            verify=False,
        )
        return response

    def _interpix_status_transaction(self, tx_id):
        """Consulta status de uma transação Inter Pix"""
        response = requests.request(
            "GET",
            url_join(INTERPIX[self.state], f"pix/v1/cob/{tx_id}/status"),
            headers=self._interpix_header(),
            data={},
            verify=False,
        )
        return response

    def interpix_get_form_action_url(self):
        """Retorna URL para webhook de feedback"""
        return "/payment/interpix/feedback"

    def _handle_interpix_webhook(self, tx_reference, jsonrequest):
        """Processa o webhook do Inter Pix"""
        transaction_id = self.env["payment.transaction"].search(
            [
                ("callback_hash", "=", tx_reference),
                ("provider_id.provider", "=", INTERPIX_PROVIDER),
            ]
        )
        if not transaction_id:
            return False
        return transaction_id._interpix_validate_webhook(tx_reference, jsonrequest)
