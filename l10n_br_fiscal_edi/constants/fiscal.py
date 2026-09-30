# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

DOCUMENT_STATE_SENDING = "enviada"
DOCUMENT_STATE_AUTHORIZED = "autorizada"
DOCUMENT_STATE_REJECTED = "rejeitada"
DOCUMENT_STATE_DENIED = "denegada"

# Context key set on the state_edoc write done by the state machine, so that
# extensions can tell a transition from a direct write of the field.
FSM_STATE_CHANGE_CONTEXT = "l10n_br_fiscal_edi_fsm_state_change"

# Selection labels are plain strings; Odoo translates them automatically
# via the field's translate=True mechanism.  Using _() here would evaluate
# at import time before the translation registry is ready.
DOCUMENT_STATES = [
    (DOCUMENT_STATE_SENDING, "Aguardando processamento"),
    (DOCUMENT_STATE_AUTHORIZED, "Autorizada"),
    (DOCUMENT_STATE_REJECTED, "Rejeitada"),
    (DOCUMENT_STATE_DENIED, "Denegada"),
]
