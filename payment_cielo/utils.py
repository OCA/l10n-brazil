# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# The card details are sent to Cielo and come back in the response, so nothing
# that goes to the log can be trusted to be free of them. Every payload and
# every response is redacted before being logged: the card number keeps only its
# last four digits, and the security code, the holder and the expiration date
# are dropped, as neither may be stored, even in a log file.
DROPPED_KEYS = frozenset(
    {
        # Card details: a security code may not be stored anywhere, and the
        # holder and the expiration date have no reason to be in a log.
        "securitycode",
        "cvv",
        "cvc",
        "holder",
        "expirationdate",
        "cardonfile",
        # Personal data of the payer that the log does not need either.
        "email",
        "identity",
        "identitytype",
    }
)
MASKED_KEYS = frozenset({"cardnumber", "cardtoken"})
REDACTED = "***"


def redact_card_data(data):
    """Return a copy of the data without the card details.

    :param data: The payload or the response to redact.
    :return: The redacted copy, safe to log.
    """
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            normalized_key = str(key).replace("_", "").replace("-", "").lower()
            if normalized_key in DROPPED_KEYS:
                redacted[key] = REDACTED
            elif normalized_key in MASKED_KEYS:
                redacted[key] = mask_card_number(value)
            else:
                redacted[key] = redact_card_data(value)
        return redacted
    elif isinstance(data, list | tuple):
        return [redact_card_data(item) for item in data]
    return data


def mask_card_number(value):
    """Return the value with only its last four digits readable.

    :param value: The card number or the card token.
    :return: The masked value.
    :rtype: str
    """
    if not isinstance(value, str) or len(value) <= 4:
        return REDACTED
    return f"{REDACTED}{value[-4:]}"
