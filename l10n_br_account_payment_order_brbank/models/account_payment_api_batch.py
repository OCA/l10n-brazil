# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re
from decimal import Decimal

from brbank.dda import codigo_barras_da_linha
from brbank.erros import ErroBrbank, Validacao
from brbank.pagamento import (
    CapacidadePagamento,
    ContaBancaria,
    DestinoPix,
    LotePagamento,
    LoteRegistrado,
    Pagamento,
    PagamentoRegistrado,
    StatusLote,
    StatusPagamento,
    TipoChavePix,
    TipoPagamento,
)
from pydantic import ValidationError

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_datetime

from odoo.addons.account_payment_order_api.models.account_payment_api_batch import (
    PaymentApiResultUnknown,
)
from odoo.addons.account_payment_order_api.models.account_payment_api_line import (
    FINAL_STATES,
)

_logger = logging.getLogger(__name__)

STATE_MAP = {
    StatusPagamento.ACEITO: "accepted",
    StatusPagamento.RECUSADO: "refused",
    StatusPagamento.AGENDADO: "scheduled",
    StatusPagamento.EM_PROCESSAMENTO: "processing",
    StatusPagamento.PAGO: "paid",
    StatusPagamento.REJEITADO: "rejected",
    StatusPagamento.CANCELADO: "cancelled",
    StatusPagamento.DEVOLVIDO: "returned",
    StatusPagamento.INDETERMINADO: "unknown",
}
# Batch states in which an accepted line still waits for the release at the bank.
NOT_RELEASED = (
    StatusLote.ACEITO,
    StatusLote.ACEITO_PARCIAL,
    StatusLote.PENDENTE_LIBERACAO,
)
PIX_KEY_TYPES = {
    "cnpj_cpf": TipoChavePix.DOCUMENTO,
    "phone": TipoChavePix.TELEFONE,
    "email": TipoChavePix.EMAIL,
    "evp": TipoChavePix.ALEATORIA,
}


def _digits(value):
    return re.sub(r"\D", "", value or "")


def _document(partner):
    return re.sub(r"[^0-9A-Za-z]", "", partner.cnpj_cpf or partner.vat or "").upper()


def _error_text(error):
    """Only brbank masks its errors; any other text may repeat payment data."""
    return str(error) if isinstance(error, ErroBrbank) else type(error).__name__


def _amount(payline):
    return Decimal(str(round(payline.amount_currency, 2)))


def _barcode(payline):
    if payline.barcode and len(_digits(payline.barcode)) == 44:
        return _digits(payline.barcode)
    if payline.digitable_line:
        return codigo_barras_da_linha(payline.digitable_line)
    return None


def _kind(payline):
    if payline.pix_copy_paste:
        return TipoPagamento.PIX_QRCODE
    barcode = _barcode(payline)
    if barcode:
        return TipoPagamento.GUIA if barcode[0] == "8" else TipoPagamento.BOLETO
    if (
        payline.partner_pix_id
        or payline.order_id.payment_mode_id.payment_mode_domain == "pix_transfer"
    ):
        return TipoPagamento.PIX
    return TipoPagamento.TRANSFERENCIA


class AccountPaymentApiBatch(models.Model):
    _inherit = "account.payment.api.batch"

    # Provider hooks of account_payment_order_api --------------------------

    def _api_brbank_batch_key(self, payline):
        """Fail here, before any batch exists, on what the bank cannot take."""
        mode = payline.order_id.payment_mode_id
        try:
            kind = _kind(payline)
        except ValueError as error:
            raise UserError(
                _("Payment line %(line)s: %(error)s", line=payline.name, error=error)
            ) from error
        if CapacidadePagamento[kind.value] not in mode._brbank_capabilities():
            raise UserError(
                _(
                    "Payment line %(line)s is a %(kind)s, which the connection "
                    "%(connection)s cannot pay through the bank API. Nothing was "
                    "sent.",
                    line=payline.name,
                    kind=self._brbank_kind_label(kind),
                    connection=mode.bank_connection_id.name,
                )
            )
        self._brbank_payment(payline, kind, "0")
        return kind.value

    def _api_brbank_reserve(self):
        try:
            return self._brbank_run(lambda adapter: adapter.reservar_numero_lote())
        except ErroBrbank as error:
            raise UserError(
                _("The bank did not reserve a batch number: %s", error)
            ) from error

    def _api_brbank_send(self):
        lote = self._brbank_batch()
        try:
            registered = self._brbank_run(lambda adapter: adapter.pagar_lote(lote))
        except UserError:
            raise
        except Validacao as error:
            raise UserError(_("The bank refused the batch: %s", error)) from error
        except Exception as error:  # pylint: disable=broad-except
            # The bank may have it: it is checked later, never sent again.
            raise PaymentApiResultUnknown(_error_text(error)) from error
        capabilities = self._brbank_capabilities()
        lines = {}
        for payment in registered.pagamentos:
            line_id = int(payment.chave_idempotencia)
            lines[line_id] = self._brbank_result(payment, capabilities)
        return {"bank_reference": registered.id_banco, "lines": lines}

    def _api_brbank_query(self):
        kind = TipoPagamento(self.batch_key)
        lines = {}
        pending = self.line_ids.filtered(lambda line: line.state not in FINAL_STATES)
        if not pending:
            return {"lines": lines}
        capabilities = self._brbank_capabilities()
        batch_status = None
        if CapacidadePagamento.LOTE_LOCAL not in capabilities:
            # The batch state tells whether the release already happened at the bank.
            reference = self.bank_reference
            registered = self._brbank_run(
                lambda adapter: adapter.consultar_lote(reference, kind)
            )
            batch_status = registered.status
            if not all(pending.mapped("bank_reference")):
                # The send answer was lost: take the line ids from the batch, in order.
                for line, payment in zip(
                    self.line_ids.sorted("id"), registered.pagamentos, strict=False
                ):
                    lines[line.id] = self._brbank_result(
                        payment, capabilities, batch_status
                    )
                return {"lines": lines}
        with_reference = pending.filtered("bank_reference")
        for line in pending - with_reference:
            lines[line.id] = {"state": "unknown", "reason": self._brbank_check_text()}
        references = {line.id: line.bank_reference for line in with_reference}
        if not references:
            return {"lines": lines}

        async def query(adapter):
            answers = {}
            for line_id, reference in references.items():
                try:
                    answers[line_id] = await adapter.consultar_pagamento(
                        reference, kind
                    )
                except ErroBrbank as error:
                    answers[line_id] = error
            return answers

        for line_id, answer in self._brbank_run(query).items():
            lines[line_id] = (
                {"reason": str(answer)[:250]}
                if isinstance(answer, ErroBrbank)
                else self._brbank_result(answer, capabilities, batch_status)
            )
        return {"lines": lines}

    def _api_brbank_cancel(self, api_lines):
        if CapacidadePagamento.CANCELAMENTO not in self._brbank_capabilities():
            raise UserError(
                _(
                    "The connection %s cannot cancel payments through the bank "
                    "API: cancel them in the bank channel.",
                    self.order_id.payment_mode_id.bank_connection_id.name,
                )
            )
        account = self._brbank_debit_account()
        references = tuple(api_lines.mapped("bank_reference"))
        try:
            self._brbank_run(
                lambda adapter: adapter.cancelar_pagamentos(account, references)
            )
        except Validacao as error:
            raise UserError(str(error)) from error
        return {"lines": {line.id: {"state": "cancelled"} for line in api_lines}}

    # Authorization of a bank without batches -------------------------------

    def _brbank_lines_to_authorize(self):
        return self.line_ids.filtered(
            lambda line: line.state == "awaiting_release" and line.bank_reference
        )

    def _brbank_registered_batch(self):
        """The batch as the adapter gave it at send time, from what is stored."""
        mode = self.order_id.payment_mode_id
        bank = mode.bank_connection_id._l10n_br_bank_payment_adapter_class().banco
        return LoteRegistrado(
            banco=bank,
            id_banco=self.bank_reference,
            tipo=TipoPagamento(self.batch_key),
            status=StatusLote.PENDENTE_LIBERACAO,
            pagamentos=tuple(
                PagamentoRegistrado(
                    banco=bank,
                    id_banco=line.bank_reference,
                    status=StatusPagamento.ACEITO,
                    chave_idempotencia=str(line.id),
                    valor=_amount(line.payment_line_id),
                    data=line.payment_line_id.date,
                )
                for line in self._brbank_lines_to_authorize()
            ),
        )

    def _brbank_authorize(self):
        """Authorize in dedicated cursors, as ``_api_send``: "sending" is committed
        before the call, so an interrupted call is checked at the bank."""
        self.ensure_one()
        with self.env.registry.cursor() as cr:
            batch = self.with_env(self.env(cr=cr))
            lines = batch._brbank_lines_to_authorize()
            if batch.state != "sent" or not lines:
                return
            order = batch.order_id
            order.payment_mode_id.bank_connection_id._l10n_br_bank_payment_config(
                batch._brbank_adapter_class(),
                order.payment_mode_id,
                order.journal_id.bank_account_id,
            )
            batch.sudo().write({"state": "sending", "date_sent": fields.Datetime.now()})
            order.message_post(
                body=_(
                    "%(user)s authorized %(count)s payment(s) at the bank on %(date)s.",
                    user=self.env.user.name,
                    count=len(lines),
                    date=format_datetime(batch.env, fields.Datetime.now()),
                )
            )
        with self.env.registry.cursor() as cr:
            # Keep the environment alive until the commit, or its writes are lost.
            batch = self.with_env(self.env(cr=cr))
            batch._brbank_authorize_now()
        self.env.invalidate_all()

    def _brbank_authorize_now(self):
        registered = self._brbank_registered_batch()
        account = self._brbank_debit_account()
        try:
            answer = self._brbank_run(
                lambda adapter: adapter.autorizar_lote(registered, account)
            )
        except Exception as error:  # pylint: disable=broad-except
            message = _error_text(error)
            _logger.warning("Payment batch %s not authorized: %s", self.name, message)
            self.sudo().write({"state": "uncertain", "message": message})
            return
        capabilities = self._brbank_capabilities()
        self.sudo().write({"state": "sent", "message": False})
        self._api_apply_answer(
            {
                "lines": {
                    int(payment.chave_idempotencia): self._brbank_result(
                        payment, capabilities
                    )
                    for payment in answer.pagamentos
                }
            }
        )
        self.order_id._api_update_state()

    # Helpers ---------------------------------------------------------------

    def _brbank_adapter_class(self):
        connection = self.order_id.payment_mode_id.bank_connection_id
        return connection._l10n_br_bank_payment_adapter_class()

    def _brbank_capabilities(self):
        return self.order_id.payment_mode_id._brbank_capabilities()

    def _brbank_run(self, operation):
        order = self.order_id
        mode = order.payment_mode_id
        return mode.bank_connection_id._l10n_br_bank_payment_run(
            mode, operation, order.journal_id.bank_account_id
        )

    def _brbank_kind_label(self, kind):
        return {
            TipoPagamento.BOLETO: _("boleto"),
            TipoPagamento.GUIA: _("guia"),
            TipoPagamento.PIX: _("Pix"),
            TipoPagamento.PIX_QRCODE: _("Pix copy and paste"),
            TipoPagamento.TRANSFERENCIA: _("TED"),
        }[kind]

    def _brbank_check_text(self):
        return _(
            "No answer from the bank and no identifier to ask for it: check the "
            "bank statement before paying this title again."
        )

    def _brbank_reason(self, payment):
        if payment.status is StatusPagamento.INDETERMINADO and not payment.id_banco:
            return self._brbank_check_text()
        texts = {
            "NAO_ENVIADO": _(
                "Not sent, because the bank did not answer an earlier payment. "
                "It can go in a new payment order."
            ),
            "SEM_RESPOSTA": _(
                "No answer from the bank: the payment may have been made. Odoo "
                "keeps asking the bank."
            ),
        }
        return ", ".join(texts.get(code, code) for code in payment.motivos) or False

    def _brbank_result(self, payment, capabilities, batch_status=None):
        state = STATE_MAP[payment.status]
        # Accepted at a bank with a release step or an approval in its channel.
        if state == "accepted" and capabilities & (
            CapacidadePagamento.LIBERACAO | CapacidadePagamento.LOTE_LOCAL
        ):
            released = batch_status is not None and batch_status not in NOT_RELEASED
            state = "processing" if released else "awaiting_release"
        result = {
            "state": state,
            "bank_reference": payment.id_banco,
            "reason": self._brbank_reason(payment),
            "authentication": payment.autenticacao or False,
        }
        if payment.data:
            result["date"] = payment.data
        if payment.valor is not None:
            result["amount"] = float(payment.valor)
        return result

    def _brbank_model(self, owner, model, **values):
        """Build a brbank model. The pydantic text repeats the input, with the
        documents and accounts of the payment: only its messages go out."""
        try:
            return model(**values)
        except ValidationError as error:
            raise UserError(
                _(
                    "Invalid payment data of %(owner)s: %(errors)s",
                    owner=owner,
                    errors="; ".join(item["msg"] for item in error.errors()),
                )
            ) from None

    def _brbank_account(self, owner, bank_account):
        """brbank account of a res.partner.bank (Brazilian branch and digit fields)."""
        bank = bank_account.bank_id
        return self._brbank_model(
            owner,
            ContaBancaria,
            agencia=_digits(bank_account.bra_number),
            conta=_digits(bank_account.acc_number),
            digito=(bank_account.acc_number_dig or "0").strip().upper()[:1],
            compe=_digits(bank.code_bc) or None,
            ispb=_digits(bank.ispb_number) or None,
            poupanca=bank_account.transactional_acc_type == "saving",
        )

    def _brbank_debit_account(self):
        order = self.order_id
        if not order.journal_id.bank_account_id:
            raise UserError(
                _("The bank journal of %s has no bank account.", order.name)
            )
        return self._brbank_account(order.name, order.journal_id.bank_account_id)

    def _brbank_batch(self):
        kind = TipoPagamento(self.batch_key)
        return self._brbank_model(
            self.order_id.name,
            LotePagamento,
            chave_idempotencia=f"odoo-batch-{self.id}",
            tipo=kind,
            conta_debito=self._brbank_debit_account(),
            pagamentos=tuple(
                self._brbank_payment(line.payment_line_id, kind, str(line.id))
                for line in self.line_ids
            ),
            numero=self.bank_reference or None,
        )

    def _brbank_payment(self, payline, kind, key):
        values = {
            "chave_idempotencia": key,
            "tipo": kind,
            "valor": _amount(payline),
            "data": payline.date,
            "descricao": (payline.communication or "")[:40] or None,
        }
        if kind is TipoPagamento.PIX_QRCODE:
            values["brcode"] = payline.pix_copy_paste
        elif kind in (TipoPagamento.BOLETO, TipoPagamento.GUIA):
            values["codigo_barras"] = _barcode(payline)
            if kind is TipoPagamento.BOLETO:
                values["beneficiario_documento"] = _document(payline.partner_id)
                if payline.own_number:
                    values["nosso_numero"] = payline.own_number
            else:
                # Only the boleto has its due date inside the barcode.
                values["vencimento"] = payline.ml_maturity_date or None
        elif kind is TipoPagamento.PIX:
            values["pix"] = self._brbank_pix_destination(payline)
        else:
            if not payline.partner_bank_id:
                raise UserError(_("Payment line %s has no bank account.", payline.name))
            values["conta_credito"] = self._brbank_account(
                payline.name, payline.partner_bank_id
            )
            values["favorecido_documento"] = _document(payline.partner_id)
            values["favorecido_nome"] = (payline.partner_id.name or "")[:140] or None
        return self._brbank_model(payline.name, Pagamento, **values)

    def _brbank_pix_destination(self, payline):
        key = payline.partner_pix_id
        if key:
            return self._brbank_model(
                payline.name,
                DestinoPix,
                tipo_chave=PIX_KEY_TYPES[key.key_type],
                chave=key.key,
            )
        if not payline.partner_bank_id:
            raise UserError(
                _("Payment line %s has no Pix key nor bank account.", payline.name)
            )
        return self._brbank_model(
            payline.name,
            DestinoPix,
            conta=self._brbank_account(payline.name, payline.partner_bank_id),
            documento=_document(payline.partner_id),
            nome=(payline.partner_id.name or "")[:140] or None,
        )
