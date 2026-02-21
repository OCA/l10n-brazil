# Copyright (C) 2023 KMEE Informática LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

DFE_VERSIONS = [("1.01", "1.01")]

DFE_VERSION_DEFAULT = "1.01"

DFE_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]

DFE_ENVIRONMENT_DEFAULT = "2"

OP_TYPE_ENTRADA = ("0", "Entrada")
OP_TYPE_SAIDA = ("1", "Saída")

OPERATION_TYPE = [OP_TYPE_ENTRADA, OP_TYPE_SAIDA]


SIT_NFE_AUTORIZADA = ("1", "Autorizada")
SIT_NFE_CANCELADA = ("2", "Cancelada")
SIT_NFE_DENEGADA = ("3", "Denegada")
SITUACAO_NFE = [SIT_NFE_AUTORIZADA, SIT_NFE_CANCELADA, SIT_NFE_DENEGADA]
