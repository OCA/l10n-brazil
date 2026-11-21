# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Codigos de receita do registro Y570 e o que o PVA exige de cada um.

Copiado das regras de campo do PVA da ECF 12.2.8 (leiaute 9, descritor 9002),
as que o descritor liga aos campos do Y570: RegraCodRecOrpPub e
RegraCodRecOrpPubNao (IND_ORG_PUB), RegraCodRecIrRetV2 (IR_RET) e
RegraCodRecCsllRet1002V1 (CSLL_RET).
"""

# Codigos aceitos com IND_ORG_PUB = "S" (retencao por orgao publico).
ORGAO_PUBLICO = frozenset(
    "4085 4397 5928 5936 5944 6147 6175 6188 6190 6228 6256 8739 8767 8850 "
    "8863 9060 9997 1895".split()
)

# Codigos aceitos com IND_ORG_PUB = "N".
NAO_ORGAO_PUBLICO = frozenset(
    "0916 0924 1708 3277 3280 3426 5204 5232 5273 5557 5706 5928 5936 5944 "
    "5952 5987 6800 6813 8045 8468 9385 9998 9999".split()
)

# Codigos que exigem IR_RET maior que zero.
EXIGE_IR_RET = frozenset(
    "5928 5936 5944 6147 6175 6188 6190 6256 8739 8767 8850 8863 9060 9997 "
    "0916 0924 1708 3277 3280 3426 5204 5232 5273 5557 5706 6800 6813 8045 "
    "8468 9385 9999".split()
)

# Codigos que exigem CSLL_RET maior que zero.
EXIGE_CSLL_RET = frozenset(
    "4085 4397 6147 6175 6188 6190 6228 8739 8767 8850 8863 9060 9997 5952 "
    "5987 9998".split()
)
