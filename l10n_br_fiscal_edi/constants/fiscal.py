# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _

DOCUMENT_STATE_SEND = "authorized"
DOCUMENT_STATE_AUTHORIZED = "authorized"
DOCUMENT_STATE_REJECTED = "rejected"

DOCUMENT_STATES = [
    (DOCUMENT_STATE_SEND, _("Sent")),
    (DOCUMENT_STATE_AUTHORIZED, _("Authorized")),
    (DOCUMENT_STATE_REJECTED, _("Rejected")),
]