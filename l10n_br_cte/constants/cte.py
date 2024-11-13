# Copyright (C) 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

CTE_VERSIONS = [("4.00", "4.00")]

CTE_VERSION_DEFAULT = "4.00"

CTE_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]

CTE_ENVIRONMENT_DEFAULT = "2"

CTE_EMIT_TYPES = [
    ("1", "1 - Prestador de serviço de transporte"),
    ("2", "2 - Transportador de Carga Própria"),
    ("3", "3 - Prestador de serviço de transporte que emitirá CT-e Globalizado"),
]

CTE_EMIT_TYPE_DEFAULT = "2"

CTE_TRANSP_TYPE = [
    ("1", "Empresa de Transporte de Cargas – ETC"),
    ("2", "Transportador Autônomo de Cargas – TAC"),
    ("3", "Cooperativa de Transporte de Cargas – CTC"),
]

CTE_TRANSP_TYPE_DEFAULT = "1"

CTE_TRANSMISSIONS = [
    ("1", "Emissão Normal"),
    ("2", "Contingência Off-Line"),
    ("3", "Regime Especial NFF"),
]

CTE_TRANSMISSION_DEFAULT = "1"

CTE_EMISSION_PROCESSES = [("0", "Emissão de CTe com aplicativo do contribuinte")]

CTE_EMISSION_PROCESS_DEFAULT = "0"

CTE_TYPE = [
    ("0", "CT-e Normal"),
    ("1", "CT-e de Complemento de Valores"),
    ("3", "CT-e de Substituição"),
]

CTE_TYPE_DEFAULT = "0"
