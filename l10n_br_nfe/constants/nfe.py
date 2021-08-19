# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

NFE_VERSIONS = [("1.10", "1.10"), ("2.00", "2.00"), ("3.10", "3.10"), ("4.00", "4.00")]


NFE_VERSION_DEFAULT = "4.00"


NFE_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]


NFE_ENVIRONMENT_DEFAULT = "2"


NFE_TRANSMISSIONS = [
    ("1", "Emissão Normal"),
    ("2", "Contingência FS-IA"),
    ("3", "Contingência SCAN"),
    ("4", "Contingência EPEC"),
    ("5", "Contingência FS-DA"),
    ("6", "Contingência SVC-AN"),
    ("7", "Contingência SVC-RS"),
    ("9", "Contingência off-line da NFC-e"),
]


NFE_TRANSMISSION_DEFAULT = "1"


NFE_DANFE_LAYOUTS = [
    ("0", "Sem geração de DANFE;"),
    ("1", "DANFE normal, Retrato;"),
    ("2", "DANFE normal, Paisagem;"),
    ("3", "DANFE Simplificado;"),
]


NFE_DANFE_LAYOUT_DEFAULT = "1"


NFCE_DANFE_LAYOUTS = [
    ("4", "DANFE NFC-e;"),
    ("5", "DANFE NFC-e por email"),
]


NFCE_DANFE_LAYOUT_DEFAULT = "4"
