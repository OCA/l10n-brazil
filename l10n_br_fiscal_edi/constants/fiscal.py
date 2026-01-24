# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _

DOCUMENT_STATE_SENDING = "sending"
DOCUMENT_STATE_AUTHORIZED = "authorized"
DOCUMENT_STATE_REJECTED = "rejected"
DOCUMENT_STATE_DENIED = "denied"

DOCUMENT_STATES = [
    (DOCUMENT_STATE_SENDING, _("Sending")),
    (DOCUMENT_STATE_AUTHORIZED, _("Authorized")),
    (DOCUMENT_STATE_REJECTED, _("Rejected")),
    (DOCUMENT_STATE_DENIED, _("Denied")),
]
