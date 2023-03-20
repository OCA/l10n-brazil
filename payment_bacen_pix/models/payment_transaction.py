# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import hmac
import json
import logging
from datetime import datetime

from werkzeug.urls import url_join

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import consteq, ustr

_logger = logging.getLogger(__name__)


BACENPIX_STATUS_CREATED = 0
BACENPIX_STATUS_PAID = 1
BACENPIX_STATUS_REJECTED = 2
BACENPIX_STATUS_EXPIRED = 3
BACENPIX_STATUS_REFUNDED = 4


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    bacenpix_date_due = fields.Datetime()
    bacenpix_qrcode = fields.Char()
    bacenpix_currency = fields.Char()
    bacenpix_amount = fields.Float()

    def _get_processing_info(self):
        # Devolver Dados do QRCODE
        res = super()._get_processing_info()
        if self.acquirer_id.provider == "bacenpix":
            if self.state == "draft":
                vals = {
                    "message_to_display": """
                        <span>
                            <h6> PIX: {} </h6>
                            <img src="/report/barcode/QR/{}?width=200&amp;height=200"/>
                            </br>
                            <div class="badge pull-right">
                                <h5>{} {}</h5>
                            </div>
                        </span>
                        """.format(
                        self.bacenpix_qrcode,
                        self.bacenpix_qrcode,
                        self.amount,
                        self.currency_id.name,
                    ),
                }
                res.update(vals)
            if self.state == "pending":
                vals = {
                    "message_to_display": """
                        <h5> <bold> Confirmações Pendentes 1 de 3 </bold></h5>
                    """,
                }
                res.update(vals)
        return res

    def action_bacenpix_check_transaction_status(self):
        for record in self:
            record._bacenpix_check_transaction_status()

    def _bacenpix_check_transaction_status(self, post=None):
        if post:
            _logger.info(post)

        response = self.acquirer_id._bacenpix_status_transaction(
            self.acquirer_reference
        )
        response_data = response.json()

        if response_data.get("status") == BACENPIX_STATUS_CREATED:
            _logger.info("BACENPIX_STATUS_CREATED")
            self._set_transaction_pending()
        elif response_data.get("status") == BACENPIX_STATUS_PAID:
            _logger.info("BACENPIX_STATUS_PAID")
            self._set_transaction_done()
            self._post_process_after_done()
        elif response_data.get("status") == BACENPIX_STATUS_REJECTED:
            _logger.info("BACENPIX_STATUS_REJECTED")
            self._set_transaction_error()
        elif response_data.get("status") == BACENPIX_STATUS_EXPIRED:
            _logger.info("BACENPIX_STATUS_EXPIRED")
            self._set_transaction_cancel()
            self.invoice_ids.button_draft()
            self.invoice_ids.button_cancel()
        elif response_data.get("status") == BACENPIX_STATUS_REFUNDED:
            _logger.info("BACENPIX_STATUS_REFUNDED")

    def _bacenpix_validate_webhook(self, valid_token, post):
        callback_hash = self._bacenpix_generate_callback_hash(self.reference)
        if not consteq(ustr(valid_token), callback_hash):
            _logger.warning("Invalid callback signature for transaction %d" % (self.id))
            return False
        _logger.info("Invalid callback signature for transaction %d" % (self.id))
        return self._bacenpix_check_transaction_status(post)

    def _bacenpix_generate_callback_hash(self, reference):
        secret = self.env["ir.config_parameter"].sudo().get_param("database.secret")
        return hmac.new(
            secret.encode("utf-8"), reference.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def bacenpix_create(self, values):
        """Compleate the values used to create the payment.transaction"""

        partner_id = self.env["res.partner"].browse(values.get("partner_id", []))
        self.env["res.currency"].browse(values.get("currency_id", []))
        acquirer_id = self.env["payment.acquirer"].browse(values.get("acquirer_id", []))

        due = fields.Date.context_today(self)
        due = datetime.combine(due, datetime.max.time())

        base_url = acquirer_id.get_base_url()

        callback_hash = self._bacenpix_generate_callback_hash(values.get("reference"))

        webhook = url_join(base_url, "/webhook/{}".format(callback_hash))
        _logger.info(webhook)

        payload = json.dumps(
            {
                "calendario": {
                    "expiracao": str(acquirer_id.bacen_pix_expiration),
                },
                "devedor": {
                    "cpf": partner_id.cnpj_cpf.replace(".", "").replace("-", ""),
                    "nome": values.get("partner_name"),
                },
                "valor": {
                    "original": str(values.get("amount")),
                },
                "chave": str(acquirer_id.bacen_pix_key),
            }
        )

        txid = values.get("tx_id")
        response = acquirer_id._bacenpix_new_transaction(txid, payload)
        response_data = response.json()
        if not response.ok:
            raise ValidationError(
                _("Payload Error {type} \n {message}".format(**response_data))
            )
        else:
            _logger.info(response_data)
            return dict(
                callback_hash=callback_hash,
                bacenpix_currency=response_data.get("currency"),
                bacenpix_amount=response_data.get("amount"),
                bacenpix_date_due=due,
                bacenpix_qrcode=response_data.get("qrcode"),
                date=datetime.now(),
                criacao=response_data.get("criacao"),
                expiracao=response_data.get("expiracao"),
                location=response_data.get("location"),
                textoImagemQRcode=response_data.get("textoImagemQRcode"),
                txid=response_data.get("txid"),
                chave=response_data.get("chave"),
                state=response_data.get("ok"),
                state_message=response_data.get("text"),
            )
