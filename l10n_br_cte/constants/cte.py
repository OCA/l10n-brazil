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

CTE_INDIETOMA = [
    ("1", "Contribuinte ICMS"),
    ("2", "Contribuinte isento de inscrição"),
    ("9", "Não Contribuinte"),
]

CTE_INDIETOMA_DEFAULT = "1"

CTE_TPSERV = [
    ("0", "Normal"),
    ("1", "Subcontratação"),
    ("2", "Redespacho"),
    ("3", "Redespacho Intermediário"),
    ("4", "Serviço Vinculado a Multimodal"),
]

CTE_TPSERV_DEFAULT = "0"

CTE_TPEMIS = [
    ("1", "Normal"),
    ("3", "Regime Especial NFF"),
    ("4", "EPEC pela SVC"),
    ("5", "Contingência FSDA"),
    ("7", "Autorização pela SVC-RS"),
    ("8", "Autorização pela SVC-SP"),
]

CTE_TPEMIS_DEFAULT = "1"

CTE_TPIMP = [
    ("1", "Retrato"),
    ("2", "Paisagem."),
]

CTE_TPIMP_DEFAULT = "1"


CTE_ICMS_SUB_TAGS = [
    "ICMS00",
    "ICMS20",
    "ICMS45",
    "ICMS60",
    "ICMS90",
    "ICMSOutraUF",
    "ICMSSN",
]

CTE_ICMS_SELECTION = list(map(lambda tag: (f"cte40_{tag}", tag), CTE_ICMS_SUB_TAGS))

CTE_CST = [
    ("00", "00 - Tributação normal ICMS"),
    ("20", "20 - Tributação com BC reduzida do ICMS"),
    ("45", "45 - ICMS Isento, não Tributado ou diferido"),
    ("60", "60 - ICMS cobrado por substituição tributária"),
    ("90", "90 - ICMS outros"),
    ("90", "90 - ICMS Outra UF"),
    ("01", "01 - Simples Nacional"),
]
