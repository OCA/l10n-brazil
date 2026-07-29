# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Endpoints of the PagBank (PagSeguro) API.
# See https://developer.pagbank.com.br/docs/apis-pagbank
API_URLS = {
    "test": "https://sandbox.api.pagseguro.com",
    "prod": "https://api.pagseguro.com",
}

# PagBank settles in BRL only.
SUPPORTED_CURRENCIES = ["BRL"]

# Mapping of charge statuses on PagBank side to transaction states.
# See https://developer.pagbank.com.br/reference/objeto-charge
PAYMENT_STATUS_MAPPING = {
    "pending": ("WAITING", "IN_ANALYSIS"),
    "authorized": ("AUTHORIZED",),
    "done": ("PAID", "AVAILABLE"),
    "cancel": ("CANCELED",),
    "error": ("DECLINED",),
}

# The maximum length of the soft descriptor, as enforced by PagBank.
SOFT_DESCRIPTOR_MAX_LENGTH = 17
