# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

NFE_VERSIONS = [("1.10", "1.10"), ("2.00", "2.00"), ("3.10", "3.10"), ("4.00", "4.00")]


NFE_VERSION_DEFAULT = "4.00"


NFE_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]


NFE_ENVIRONMENT_DEFAULT = "2"


NFE_TRANSMISSIONS = [
    ("1", "1 - Emissão Normal"),
    ("2", "2 - Contingência FS-IA (Não Implementado)"),
    ("3", "3 - Contingência SCAN (Não Implementado)"),
    ("4", "4 - Contingência EPEC (Não Implementado)"),
    ("5", "5 - Contingência FS-DA (Não Implementado)"),
    ("6", "6 - Contingência SVC-AN (Não Implementado)"),
    ("7", "7 - Contingência SVC-RS (Não Implementado)"),
    ("9", "9 - Contingência off-line da NFC-e (Não Implementado)"),
]


NFE_TRANSMISSION_DEFAULT = "1"
