# Copyright (C) 2023 Felipe Zago - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

MDFE_VERSIONS = [("3.00", "3.00")]

MDFE_VERSION_DEFAULT = "3.00"

MDFE_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]

MDFE_ENVIRONMENT_DEFAULT = "2"

MDFE_EMIT_TYPES = [
    ("1", "1 - Prestador de serviço de transporte"),
    ("2", "2 - Transportador de Carga Própria"),
    ("3", "3 - Prestador de serviço de transporte que emitirá CT-e Globalizado"),
]

MDFE_EMIT_TYPE_DEFAULT = "2"

MDFE_TRANSP_TYPE = [
    ("1", "Empresa de Transporte de Cargas – ETC"),
    ("2", "Transportador Autônomo de Cargas – TAC"),
    ("3", "Cooperativa de Transporte de Cargas – CTC"),
]

MDFE_TRANSP_TYPE_DEFAULT = "1"

MDFE_TRANSMISSIONS = [
    ("1", "Emissão Normal"),
    ("2", "Contingência Off-Line"),
    ("3", "Regime Especial NFF"),
]

MDFE_TRANSMISSION_DEFAULT = "1"

MDFE_EMISSION_PROCESSES = [("0", "Emissão de MDFe com aplicativo do contribuinte")]

MDFE_EMISSION_PROCESS_DEFAULT = "0"
