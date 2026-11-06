# Copyright (C) 2023 KMEE Informática LTDA
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

SIT_NFE_AUTORIZADA = ("1", "Autorizada")
SIT_NFE_DENEGADA = ("2", "Denegada")
SIT_NFE_CANCELADA = ("3", "Cancelada")
SITUACAO_NFE = [SIT_NFE_AUTORIZADA, SIT_NFE_DENEGADA, SIT_NFE_CANCELADA]

# Official cancellation events from the DF-e distribution. A correction
# letter (110110) and a manifestation do not belong here.
NFE_CANCEL_EVENT_CODES = ("110111", "110112")
