# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

NFSE_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]


NFSE_ENVIRONMENT_DEFAULT = "2"


OPERATION_NATURE = [
    ("1", "Tributação no município"),
    ("2", "Tributação fora do município"),
    ("3", "Isenção"),
    ("4", "Imune"),
    ("5", "Exigibilidade suspensa por decisão judicial"),
    ("6", "Exigibilidade suspensa por procedimento administrativo"),
]


RPS_TYPE = [
    ("1", "Recibo provisório de Serviços"),
    ("2", "RPS Nota Fiscal Conjugada (Mista)"),
    ("3", "Cupom"),
]


TAXATION_SPECIAL_REGIME = [
    ("1", "Microempresa Municipal"),
    ("2", "Estimativa"),
    ("3", "Sociedade de Profissionais"),
    ("4", "Cooperativa"),
    ("5", "Microempresario Individual(MEI)"),
    ("6", "Microempresario e Empresa de Pequeno Porte(ME EPP)"),
]


ISSQN_TO_TRIBUTACAO_ISS = {
    "1": "1",  # Exigível → Operação tributável
    "2": "3",  # Não incidência → Não Incidência
    "3": "3",  # Isenção → Não Incidência
    "4": "2",  # Exportação → Exportação de serviço
    "5": "4",  # Imunidade → Imunidade
    "6": "1",  # Suspensa (Judicial) → Operação tributável
    "7": "1",  # Suspensa (Administrativo) → Operação tributável
}

# Foreign trade group (comExt) of the NFS-e Nacional, same codes as the
# TSModoPrestacao, TSVincPrest, TSMecAFComExPrest and TSMecAFComExToma types.
FOREIGN_TRADE_MODE = [
    ("0", "Unknown"),
    ("1", "Cross-border"),
    ("2", "Consumption in Brazil"),
    ("3", "Temporary movement of individuals"),
    ("4", "Consumption abroad"),
]
FOREIGN_TRADE_LINK = [
    ("0", "No link with the provider/recipient"),
    ("1", "Controlled"),
    ("2", "Controlling"),
    ("3", "Affiliated"),
    ("4", "Head office"),
    ("5", "Branch"),
    ("6", "Other link"),
    ("9", "Unknown"),
]
FOREIGN_TRADE_SUPPORT_PROVIDER = [
    ("00", "Unknown"),
    ("01", "None"),
    ("02", "ACC"),
    ("03", "ACE"),
    ("04", "BNDES-Exim post-shipment"),
    ("05", "BNDES-Exim pre-shipment"),
    ("06", "FGE"),
    ("07", "PROEX equalization"),
    ("08", "PROEX financing"),
]
FOREIGN_TRADE_SUPPORT_RECIPIENT = [("00", "Unknown"), ("01", "None")] + [
    (f"{n:02d}", f"Mechanism {n:02d}") for n in range(2, 27)
]
