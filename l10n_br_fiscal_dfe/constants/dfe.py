# Copyright (C) 2023 KMEE Informática LTDA
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from datetime import timedelta

DFE_VERSIONS = [("1.01", "1.01")]

DFE_VERSION_DEFAULT = "1.01"

DFE_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]

DFE_ENVIRONMENT_DEFAULT = "2"

OP_TYPE_ENTRADA = ("0", "Entrada")
OP_TYPE_SAIDA = ("1", "Saída")

OPERATION_TYPE = [OP_TYPE_ENTRADA, OP_TYPE_SAIDA]


SIT_NFE_AUTORIZADA = ("1", "Autorizada")
SIT_NFE_DENEGADA = ("2", "Denegada")
SIT_NFE_CANCELADA = ("3", "Cancelada")
SITUACAO_NFE = [SIT_NFE_AUTORIZADA, SIT_NFE_DENEGADA, SIT_NFE_CANCELADA]

# SEFAZ distribution response codes (NT 2014.002)
CSTAT_SUCCESS = "138"  # Documento(s) localizado(s)
CSTAT_NO_DOCS = "137"  # Nenhum documento localizado para o Contribuinte
CSTAT_CONSUMO_INDEVIDO = "656"  # Consumo Indevido (rate limit — aguardar 1h)

# Scheduling intervals for dfe_next_query (NT 2014.002 compliance)
DFE_INTERVAL_SUCCESS = timedelta(minutes=10)  # 138: docs found, wait for SEFAZ
DFE_INTERVAL_NO_DOCS = timedelta(hours=1, minutes=1)  # 137: no docs (cooldown + margin)
DFE_INTERVAL_RATE_LIMITED = timedelta(hours=1, minutes=1)  # 656: rate limit + margin
DFE_INTERVAL_ERROR = timedelta(minutes=15)  # Network/exception error

EVENT_TYPE_LABELS = {
    "210200": "Confirmação da Operação",
    "210210": "Ciência da Operação",
    "210220": "Desconhecimento da Operação",
    "210240": "Operação não Realizada",
    "110110": "Carta de Correção",
    "110111": "Cancelamento",
    "110112": "Cancelamento por Substituição",
    "110140": "EPEC",
}

DFE_DESCRIPTION_MAP = {
    "procNFe": "XML NF-e completo (procNFe) via distribuição DF-e",
    "resNFe": "Resumo de NF-e (resNFe) via distribuição DF-e",
    "procEventoNFe": "XML de evento de NF-e (procEventoNFe) via distribuição DF-e",
    "resEvento": "Resumo de evento de NF-e (resEvento) via distribuição DF-e",
}
