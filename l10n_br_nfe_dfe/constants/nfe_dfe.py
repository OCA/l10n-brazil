# Copyright (C) 2023 KMEE Informática LTDA
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

SIT_NFE_AUTORIZADA = ("1", "Autorizada")
SIT_NFE_DENEGADA = ("2", "Denegada")
SIT_NFE_CANCELADA = ("3", "Cancelada")
SITUACAO_NFE = [SIT_NFE_AUTORIZADA, SIT_NFE_DENEGADA, SIT_NFE_CANCELADA]

# The acknowledgement (ciencia) of the operation is only accepted until 10 days
# after the authorization (Ajuste SINIEF 07/05, clause 15-C, paragraph 4)
ACKNOWLEDGEMENT_DAYS = 10

# Registering a manifestation of the recipient at the tax authority speaks for the
# company with its certificate: it takes the group of the NF-e user, not the fiscal one.
MANIFESTATION_GROUP = "l10n_br_nfe.group_user"
