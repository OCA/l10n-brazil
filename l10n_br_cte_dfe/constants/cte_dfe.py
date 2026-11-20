# Copyright 2026 Engenere.
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

# The CT-e distribution service has no summary payload (resCTe), so the
# document situation is only known from the complete XML (authorized) and
# from the events that follow it (cancellation).
SIT_CTE_AUTORIZADA = ("1", "Autorizada")
SIT_CTE_CANCELADA = ("3", "Cancelada")
SITUACAO_CTE = [SIT_CTE_AUTORIZADA, SIT_CTE_CANCELADA]

CTE_EVENT_CANCELAMENTO = "110111"

# Events distributed by CTeDistribuicaoDFe (NT 2015.002 v1.05)
CTE_EVENT_LABELS = {
    "110110": "Carta de Correção",
    "110111": "Cancelamento",
    "110113": "EPEC",
    "110160": "Registros do Multimodal",
    "110170": "Informações da GTV",
    "110180": "Comprovante de Entrega",
    "110181": "Cancelamento do Comprovante de Entrega",
    "110190": "Insucesso na Entrega",
    "110191": "Cancelamento do Insucesso na Entrega",
    "610110": "Prestação do Serviço em Desacordo",
    "610111": "Cancelamento da Prestação em Desacordo",
}

# Schemas distributed by the service, mapped to the root element that
# holds the document (``<root>.<element>.infCte``). procEventoCTe is
# handled apart.
CTE_PROC_SCHEMAS = {
    "procCTe": "CTe",
    "procCTeOS": "CTeOS",
    "procGTVe": "GTVe",
    "procCTeSimp": "CTeSimp",
}

# Only the CT-e model 57 can be imported as a fiscal document today.
CTE_IMPORTABLE_SCHEMAS = ("procCTe",)
