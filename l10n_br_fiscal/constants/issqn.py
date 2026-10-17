# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

ISSQN_ELIGIBILITY = [
    ("1", "Exigível"),
    ("2", "Não incidência"),
    ("3", "Isenção"),
    ("4", "Exportação"),
    ("5", "Imunidade"),
    ("6", "Exigibilidade Suspensa por Decisão Judicial"),
    ("7", "Exigibilidade Suspensa por Processo Administrativo"),
]


# "Exigivel" e o caso comum de uma nota de servico. Com o default em "2",
# nao incidencia, toda linha nasce declarando que o ISS nao incide: o mapa
# ISSQN_TO_TRIBUTACAO_ISS manda isso para tribISSQN 3 no DPS da NFS-e
# nacional, e a nota sai dizendo nao incidencia ao lado de uma aliquota de
# ISS, contradicao que uma nota real do emissor nacional nao tem.
ISSQN_ELIGIBILITY_DEFAULT = "1"

ISSQN_INCENTIVE = [
    ("1", "Sim"),
    ("2", "Não"),
]


ISSQN_INCENTIVE_DEFAULT = "2"
