# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)

INT_CURRENCIES = [
    "BRL",
    "XAF",
    "XPF",
    "CLP",
    "KMF",
    "DJF",
    "GNF",
    "JPY",
    "MGA",
    "PYG",
    "RWF",
    "KRW",
    "VUV",
    "VND",
    "XOF",
]


class PaymentTransactionCielo(models.Model):
    _inherit = "payment.transaction"

    cielo_s2s_capture_link = fields.Char(string="Capture Link")
    cielo_s2s_void_link = fields.Char(string="Void Link")
    cielo_s2s_check_link = fields.Char(string="Check Link")

    def _get_specific_rendering_values(self, processing_values):
        self.ensure_one()
        return {
            "api_url": "/payment/cielo/s2s/create",
            "tx_id": self.id,
            "provider": self.provider_id,
            "amount": self.amount,
            "currency": self.currency_id,
            "reference": self.reference,
            "partner_name": self.partner_id.name or "",
        }

    def _get_processing_values(self):
        res = super()._get_processing_values()
        if self.provider_code != "cielo":
            return res

        self.ensure_one()

        # Garante que o redirect_url sempre existe
        res.update(
            {
                "redirect_url": f"/payment/cielo/payment?tx_id={self.id}",
            }
        )
        return res

    def _cielo_tokenize(self, card_data):
        """Tokeniza um cartão no endpoint Cielo."""
        provider = self.provider_id
        api_host = provider._get_cielo_api_url()
        api_url = f"https://{api_host}/1/card"

        # Processa a data de expiração
        expiry = card_data.get("card_expiry", "").replace(" ", "")
        if "/" in expiry:
            mm, yy = (p.strip() for p in expiry.split("/"))
        else:
            mm, yy = expiry[:2], expiry[-2:]

        # Converte ano de 2 dígitos para 4 dígitos
        try:
            year4 = int(yy)
            if year4 < 100:
                current_century = (fields.Datetime.now().year // 100) * 100
                year4 = current_century + int(yy)
        except Exception:
            year4 = fields.Datetime.now().year

        cielo_expiry = f"{mm.zfill(2)}/{year4}"

        # Ajusta a bandeira
        brand = (card_data.get("card_brand") or "").strip()
        if brand.lower() in ["mastercard", "master"]:
            brand = "Master"
        elif brand.lower() == "visa":
            brand = "Visa"

        payload = {
            "CustomerName": self.partner_id.name or "",
            "CardNumber": card_data.get("card_number", "").replace(" ", ""),
            "Holder": card_data.get("card_holder", ""),
            "ExpirationDate": cielo_expiry,
            "Brand": brand,
        }

        _logger.info(
            "Cielo tokenize payload: %s",
            pprint.pformat({**payload, "CardNumber": "***HIDDEN***"}),
        )

        try:
            r = requests.post(
                api_url,
                json=payload,
                headers=provider._get_cielo_api_headers(),
                timeout=30,
            )
            r.raise_for_status()
            response = r.json()
        except requests.RequestException as e:
            _logger.exception("Cielo tokenize request failed")
            raise ValueError(f"Erro na tokenização: {str(e)}")
        except ValueError as e:
            _logger.exception("Cielo returned invalid JSON for tokenize")
            raise ValueError(f"Resposta inválida da Cielo: {str(e)}")

        _logger.debug("Cielo tokenize response: %s", pprint.pformat(response))
        return response

    def _create_cielo_charge(self, provider_ref=None, tokenid=None, email=None):
        """Cria o payload para efetuar a cobrança na Cielo e envia a requisição."""
        self.ensure_one()
        provider = self.provider_id
        api_host = provider._get_cielo_api_url()
        api_url = f"https://{api_host}/1/sales"

        card_token = tokenid or (self.token_id.cielo_token if self.token_id else None)
        if not card_token:
            raise ValueError("No card token available to create charge")

        card_brand = (self.token_id.card_brand or "").lower() if self.token_id else ""
        if card_brand in ["mastercard", "master"]:
            card_brand = "Master"
        elif card_brand == "visa":
            card_brand = "Visa"
        else:
            card_brand = "Visa"  # Padrão

        amount_cents = int(round(self.amount * 100))

        payload = {
            "MerchantOrderId": str(self.id),
            "Customer": {"Name": self.partner_id.name},
            "Payment": {
                "Type": "CreditCard",
                "Amount": amount_cents,
                "Installments": 1,
                "SoftDescriptor": (self.display_name or "")[:13],
                "CreditCard": {
                    "CardToken": card_token,
                    "Brand": card_brand,
                    "SaveCard": False,
                },
            },
        }

        _logger.info("Cielo create charge payload: %s", pprint.pformat(payload))

        try:
            r = requests.post(
                api_url,
                json=payload,
                headers=provider._get_cielo_api_headers(),
                timeout=30,
            )
            r.raise_for_status()
            res = r.json()
        except requests.RequestException as e:
            _logger.exception("Error sending create_charge to Cielo")
            raise ValueError(f"Erro na cobrança: {str(e)}")
        except ValueError as e:
            _logger.exception("Cielo returned invalid JSON for create_charge")
            raise ValueError(f"Resposta inválida da Cielo: {str(e)}")

        _logger.debug("Cielo create charge response: %s", pprint.pformat(res))

        if self.token_id:
            try:
                self.token_id.active = False
            except Exception:
                _logger.exception("Could not deactivate token")

        return res

    def cielo_s2s_do_transaction(self, card_data=None, **kwargs):
        """Executa o fluxo completo: tokenização + cobrança"""
        self.ensure_one()

        # Se recebeu dados do cartão, tokeniza primeiro
        if card_data:
            token_response = self._cielo_tokenize(card_data)
            card_token = token_response.get("CardToken") or token_response.get(
                "cardToken"
            )

            if not card_token:
                raise ValueError("Não foi possível gerar o token do cartão")

            # Cria o payment.token
            token_vals = {
                "provider_id": self.provider_id.id,
                "display_name": f"Card {card_data.get('card_brand', 'Unknown')} ****{card_data.get('card_number', '')[-4:]}",
                "cielo_token": card_token,
                "card_brand": card_data.get("card_brand", "").lower(),
                "partner_id": self.partner_id.id,
                "provider_ref": card_token,
                "verified": False,
            }

            self.token_id = self.env["payment.token"].sudo().create(token_vals)
            _logger.info("Token criado: %s", self.token_id.display_name)

        # Agora cria a cobrança
        response = self._create_cielo_charge(
            provider_ref=kwargs.get("provider_ref"),
            tokenid=kwargs.get("tokenid"),
            email=kwargs.get("email"),
        )

        return self._cielo_s2s_validate_tree(response)

    def cielo_s2s_capture_transaction(self):
        self.ensure_one()
        if not self.cielo_s2s_capture_link:
            raise ValueError("No capture link available")
        try:
            r = requests.put(
                self.cielo_s2s_capture_link,
                headers=self.provider_id._get_cielo_api_headers(),
                timeout=30,
            )
            r.raise_for_status()
            res = r.json()
        except requests.RequestException:
            _logger.exception("Cielo capture request failed")
            raise

        if (
            isinstance(res, dict)
            and res.get("ProviderReturnMessage") == "Operation Successful"
        ):
            self._set_transaction_done()
            self.execute_callback()
        else:
            self.sudo().write({"state_message": str(res)})

    def cielo_s2s_void_transaction(self):
        self.ensure_one()
        if not self.cielo_s2s_void_link:
            raise ValueError("No void link available")
        try:
            r = requests.put(
                self.cielo_s2s_void_link,
                headers=self.provider_id._get_cielo_api_headers(),
                timeout=30,
            )
            r.raise_for_status()
            res = r.json()
        except requests.RequestException:
            _logger.exception("Cielo void request failed")
            raise

        if (
            isinstance(res, dict)
            and res.get("ProviderReturnMessage") == "Operation Successful"
        ):
            self.write({"date": fields.Datetime.now(), "provider_reference": res})
            self._set_transaction_cancel()
        else:
            self.sudo().write({"state_message": str(res)})

    def _cielo_s2s_validate_tree(self, tree):
        """Valida a resposta da Cielo e atualiza a transação no Odoo 16."""
        self.ensure_one()

        if self.state != "draft":
            _logger.info(
                "Cielo: trying to validate an already validated tx (ref %s)",
                self.reference,
            )
            return True

        if isinstance(tree, dict):
            payment = tree.get("Payment") or {}
            status = payment.get("Status")

            # Se status = 1, transação aprovada
            if status == 1:
                links = payment.get("Links") or []
                for method in links:
                    rel = method.get("Rel")
                    href = method.get("Href")
                    if rel == "self":
                        self.cielo_s2s_check_link = href
                    elif rel == "capture":
                        self.cielo_s2s_capture_link = href
                    elif rel == "void":
                        self.cielo_s2s_void_link = href

                # Atualiza estado para done
                self.write(
                    {
                        "state": "done",
                        "state_message": "Pagamento autorizado",
                        "provider_reference": payment.get("PaymentId") or "",
                    }
                )

                # Marca token como verificado
                if self.token_id:
                    try:
                        self.token_id.verified = True
                    except Exception:
                        _logger.exception("Could not set token verified flag")

                return True

            else:
                # Transação falhou
                error = (
                    payment.get("ReturnMessage")
                    or tree.get("ErrorMessage")
                    or str(tree)
                )
                _logger.warning("Cielo payment failed: %s", error)
                self.write(
                    {
                        "state": "cancel",
                        "state_message": error,
                        "provider_reference": payment.get("PaymentId") or "",
                    }
                )
                return False

        elif isinstance(tree, list):
            error = (
                tree[0].get("Message")
                if tree and isinstance(tree[0], dict)
                else str(tree)
            )
            _logger.warning("Cielo returned list error: %s", error)
            self.write({"state": "cancel", "state_message": error})
            return False

        else:
            # Resposta inesperada da cielo
            _logger.warning("Cielo: unexpected response type: %s", type(tree))
            self.write({"state": "cancel", "state_message": str(tree)})
            return False
