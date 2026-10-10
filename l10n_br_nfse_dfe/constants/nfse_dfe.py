# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# ADN distribution (tomador). Distinct from the Sefin Nacional emission API.
NFSE_ADN_BASE_URLS = {
    "producao": "https://adn.nfse.gov.br",
    "producao_restrita": "https://adn.producaorestrita.nfse.gov.br",
}

NFSE_ADN_DFE_PATH = "/contribuintes/DFe"
NFSE_ADN_NFSE_PATH = "/contribuintes/NFSe"

# Sefin Nacional keeps the authorized NFS-e. ADN ``GET /NFSe/{chave}`` is 404;
# the note is ``GET /nfse/{chave}`` here, and its events stay on the ADN.
NFSE_SEFIN_BASE_URLS = {
    "producao": "https://sefin.nfse.gov.br/SefinNacional",
    "producao_restrita": "https://sefin.producaorestrita.nfse.gov.br/SefinNacional",
}
NFSE_SEFIN_NFSE_PATH = "/nfse"

NFSE_LOTE_SIZE = 50
NFSE_MAX_PAGES = 20
NFSE_ACCESS_KEY_SIZE = 50

NFSE_NOTE_TYPES = {"NFSE", "NFS-E"}
# Distributed, but not a service invoice and not an event of one.
NFSE_SKIP_DOCUMENT_TYPES = {"DPS", "CNC", "NENHUM"}
NFSE_EVENT_DOCUMENT_TYPES = {
    "EVENTO",
    "EVENT",
    "PEDIDO_REGISTRO_EVENTO",
    "PEDREGISTROEVENTO",
}

# ADN ``TipoEvento`` enum -> national event code (without the leading "e").
NFSE_EVENT_CODE_BY_NAME = {
    "CANCELAMENTO": "101101",
    "SOLICITACAO_CANCELAMENTO_ANALISE_FISCAL": "101103",
    "CANCELAMENTO_POR_SUBSTITUICAO": "105102",
    "CANCELAMENTO_DEFERIDO_ANALISE_FISCAL": "105104",
    "CANCELAMENTO_INDEFERIDO_ANALISE_FISCAL": "105105",
    "CONFIRMACAO_PRESTADOR": "202201",
    "REJEICAO_PRESTADOR": "202205",
    "CONFIRMACAO_TOMADOR": "203202",
    "REJEICAO_TOMADOR": "203206",
    "CONFIRMACAO_INTERMEDIARIO": "204203",
    "REJEICAO_INTERMEDIARIO": "204207",
    "CONFIRMACAO_TACITA": "205204",
    "ANULACAO_REJEICAO": "205208",
    "CANCELAMENTO_POR_OFICIO": "305101",
    "BLOQUEIO_POR_OFICIO": "305102",
    "DESBLOQUEIO_POR_OFICIO": "305103",
}

# A registered cancellation. A request or a denied request is not one of these.
NFSE_CANCEL_EVENT_NAMES = {
    "CANCELAMENTO",
    "CANCELAMENTO_POR_SUBSTITUICAO",
    "CANCELAMENTO_DEFERIDO_ANALISE_FISCAL",
    "CANCELAMENTO_POR_OFICIO",
}
NFSE_CANCEL_EVENT_CODES = {"101101", "105102", "105104", "305101"}

NFSE_STATE_AUTHORIZED = "1"
NFSE_STATE_CANCELLED = "3"

NFSE_STATE_LABELS = {
    NFSE_STATE_AUTHORIZED: "Authorized",
    NFSE_STATE_CANCELLED: "Cancelled",
}

NFSE_EVENT_LABELS = {
    "101101": "NFS-e Cancellation",
    "e101101": "NFS-e Cancellation",
    "CANCELAMENTO": "NFS-e Cancellation",
    "101103": "NFS-e Cancellation Request",
    "e101103": "NFS-e Cancellation Request",
    "SOLICITACAO_CANCELAMENTO_ANALISE_FISCAL": "NFS-e Cancellation Request",
    "105102": "NFS-e Cancellation by Substitution",
    "e105102": "NFS-e Cancellation by Substitution",
    "CANCELAMENTO_POR_SUBSTITUICAO": "NFS-e Cancellation by Substitution",
    "105104": "NFS-e Cancellation Accepted by the Tax Authority",
    "e105104": "NFS-e Cancellation Accepted by the Tax Authority",
    "CANCELAMENTO_DEFERIDO_ANALISE_FISCAL": (
        "NFS-e Cancellation Accepted by the Tax Authority"
    ),
    "105105": "NFS-e Cancellation Rejected by the Tax Authority",
    "e105105": "NFS-e Cancellation Rejected by the Tax Authority",
    "CANCELAMENTO_INDEFERIDO_ANALISE_FISCAL": (
        "NFS-e Cancellation Rejected by the Tax Authority"
    ),
    "305101": "NFS-e Cancellation by the Tax Authority",
    "e305101": "NFS-e Cancellation by the Tax Authority",
    "CANCELAMENTO_POR_OFICIO": "NFS-e Cancellation by the Tax Authority",
}
