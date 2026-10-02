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


# Literal of the xCondUso of the event 110110 (CC-e): the XSD accepts only the
# two enumerated texts, with and without accents. It is the one that the
# library sends, so the printed text is the registered one.
CCE_CONDITION_OF_USE = (
    "A Carta de Correcao e disciplinada pelo paragrafo 1o-A do art. 7o do "
    "Convenio S/N, de 15 de dezembro de 1970 e pode ser utilizada para "
    "regularizacao de erro ocorrido na emissao de documento fiscal, desde "
    "que o erro nao esteja relacionado com: I - as variaveis que determinam "
    "o valor do imposto tais como: base de calculo, aliquota, diferenca de "
    "preco, quantidade, valor da operacao ou da prestacao; II - a correcao "
    "de dados cadastrais que implique mudanca do remetente ou do "
    "destinatario; III - a data de emissao ou de saida."
)
