# Copyright 2023 KMEE
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
    bacenpix_criacao = fields.Char()
    bacenpix_expiracao = fields.Char()
    bacenpix_location = fields.Char()
    bacenpix_txid = fields.Char()
    bacenpix_chave = fields.Char()
    bacenpix_state = fields.Char()
    bacenpix_state_message = fields.Char()
    textoImagemQRcode = fields.Char()

    def _get_processing_info(self):
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
        callback_hash = self._bacenpix_generate_callback_hash(self.bacenpix_txid)
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
        """Complete the values used to create the payment.transaction"""
        partner_id = self.env["res.partner"].browse(values.get("partner_id", []))
        acquirer_id = self.env["payment.acquirer"].browse(values.get("acquirer_id", []))
        currency_id = acquirer_id.create_uid.currency_id

        due = fields.Date.context_today(self)
        due = datetime.combine(due, datetime.max.time())

        base_url = acquirer_id.get_base_url()

        if values.get("bacenpix_txid"):
            txid = values.get("bacenpix_txid")
        else:
            txid = (partner_id.cnpj_cpf.replace(".", "").replace("-", ""),)
        callback_hash = self._bacenpix_generate_callback_hash(str(txid))
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
                currency_id=currency_id.id,
                bacenpix_currency=response_data.get("currency"),
                bacenpix_amount=values.get("amount"),
                bacenpix_date_due=due,
                bacenpix_qrcode=response_data["textoImagemQRcode"],
                amount=values.get("amount"),
                date=datetime.now(),
                state="draft",
                textoImagemQRcode=response_data["textoImagemQRcode"],
                bacenpix_criacao=response_data["calendario"]["criacao"],
                bacenpix_expiracao=response_data["calendario"]["expiracao"],
                bacenpix_location=response_data["location"],
                bacenpix_txid=response_data["txid"],
                bacenpix_chave=response_data["chave"],
                bacenpix_state=response_data["status"],
                bacenpix_state_message=response_data["solicitacaoPagador"],
            )
