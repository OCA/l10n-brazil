# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Translation of the DDA objects of brbank to the vals of `_dda_upsert`."""

import json
from datetime import timezone

from odoo import fields

from odoo.addons.l10n_br_dda.utils import normalize_cnpj


def naive_utc(moment):
    """Naive UTC datetime of a datetime from the library (naive means UTC)."""
    if not moment:
        return False
    if moment.tzinfo:
        moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
    return moment


def debit_to_vals(debit):
    """Vals of `_dda_upsert` from a `brbank.dda.DebitoDda`; absent data stays empty."""
    moment = naive_utc(debit.atualizado_em)
    return {
        "payer_cnpj": debit.cnpj_pagador,
        "digitable_line": debit.linha_digitavel,
        "barcode": debit.codigo_barras,
        "beneficiary_vat": debit.beneficiario_documento,
        "beneficiary_name": debit.beneficiario_nome,
        "beneficiary_trade_name": debit.beneficiario_fantasia,
        "guarantor_vat": debit.sacador_documento,
        "guarantor_name": debit.sacador_nome,
        "issuer_bank": debit.banco_emissor,
        "document_number": debit.numero_documento,
        "amount": float(debit.valor),
        "discount_amount": None if debit.desconto is None else float(debit.desconto),
        "interest_amount": None if debit.juros is None else float(debit.juros),
        "fine_amount": None if debit.multa is None else float(debit.multa),
        "date_due": debit.vencimento.isoformat() if debit.vencimento else None,
        "date_limit": debit.data_limite.isoformat() if debit.data_limite else None,
        "external_id": debit.id_banco,
        "status": debit.status.value,
        "updated_at": fields.Datetime.to_string(moment) if moment else None,
        "raw_payload": json.dumps(debit.resposta_bruta, default=str, sort_keys=True),
    }


def source_key(connection):
    """`source_key` of the boletos a connection feeds into the DDA inbox."""
    return "connection:%s" % connection.id


def same_payer(connection_cnpj, payer_cnpj):
    """Whether a boleto belongs to the CNPJ of the connection."""
    return normalize_cnpj(connection_cnpj) == normalize_cnpj(payer_cnpj)
