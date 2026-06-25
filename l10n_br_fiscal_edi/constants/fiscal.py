# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _

DOCUMENT_STATE_SENDING = "enviada"
DOCUMENT_STATE_AUTHORIZED = "autorizada"
DOCUMENT_STATE_REJECTED = "rejeitada"
DOCUMENT_STATE_DENIED = "denegada"

DOCUMENT_STATES = [
    (DOCUMENT_STATE_SENDING, _("Aguardando processamento")),
    (DOCUMENT_STATE_AUTHORIZED, _("Autorizada")),
    (DOCUMENT_STATE_REJECTED, _("Rejeitada")),
    (DOCUMENT_STATE_DENIED, _("Denegada")),
]
