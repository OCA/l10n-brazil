# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Endpoints of the Cielo E-commerce API 3.0.
# See https://developercielo.github.io/manual/cielo-ecommerce
API_URLS = {
    "test": {
        "transaction": "https://apisandbox.cieloecommerce.cielo.com.br",
        "query": "https://apiquerysandbox.cieloecommerce.cielo.com.br",
    },
    "prod": {
        "transaction": "https://api.cieloecommerce.cielo.com.br",
        "query": "https://apiquery.cieloecommerce.cielo.com.br",
    },
}

# The currencies supported by Cielo. The API amounts are always in Brazilian cents.
SUPPORTED_CURRENCIES = ["BRL"]

# Mapping of transaction states on Cielo side to Odoo transaction states.
# See the "Status da transação" section of
# https://developercielo.github.io/manual/cielo-ecommerce
PAYMENT_STATUS_MAPPING = {
    "pending": (0, 12, 20),  # NotFinished, Pending, Scheduled
    "authorized": (1,),  # Authorized
    "done": (2,),  # PaymentConfirmed
    "cancel": (10, 11),  # Voided, Refunded
    "error": (3, 13),  # Denied, Aborted
}

# Card brands accepted by Cielo, keyed by the value sent in the `Brand` field.
# The values of the mapping are the prefixes (BINs) used to detect the brand from
# the card number, in the order they must be evaluated.
CARD_BRANDS = {
    "Elo": (
        "401178",
        "401179",
        "431274",
        "438935",
        "451416",
        "457393",
        "457631",
        "457632",
        "504175",
        "506699",
        "509",
        "627780",
        "636297",
        "636368",
        "650",
        "6516",
        "6550",
    ),
    "Hipercard": ("606282", "3841"),
    "Amex": ("34", "37"),
    "Diners": ("301", "305", "36", "38"),
    "Discover": ("6011", "622", "64", "65"),
    "JCB": ("35",),
    "Aura": ("50",),
    "Visa": ("4",),
    "Master": ("2", "5"),
}

# The maximum length of the soft descriptor, as enforced by Cielo.
SOFT_DESCRIPTOR_MAX_LENGTH = 13


def get_card_brand(card_number):
    """Return the Cielo brand matching the card number, or ``None``.

    Brands with more specific prefixes (Elo, Hipercard) are evaluated first so
    that they are not shadowed by the generic Visa and Master prefixes.

    :param str card_number: The card number, with or without separators.
    :return: The brand as expected by Cielo in the `Brand` field.
    :rtype: str|None
    """
    digits = "".join(char for char in (card_number or "") if char.isdigit())
    for brand, prefixes in CARD_BRANDS.items():
        if digits.startswith(prefixes):
            return brand
    return None
