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
    "2": "4",  # Não incidência → Não Incidência
    "3": "4",  # Isenção → Não Incidência
    "4": "3",  # Exportação → Exportação de serviço
    "5": "2",  # Imunidade → Imunidade
    "6": "1",  # Suspensa (Judicial) → Operação tributável
    "7": "1",  # Suspensa (Administrativo) → Operação tributável
}
