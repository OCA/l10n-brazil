# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# The card is encrypted in the browser, so no card number reaches the server,
# but the payload and the response still carry the holder, the tax id and the
# email of the payer, and the encrypted card itself is a payment credential.
# Nothing of that belongs in a log file.
DROPPED_KEYS = frozenset(
    {
        "encrypted",
        "holder",
        "securitycode",
        "cvv",
        "expmonth",
        "expyear",
        "taxid",
        "email",
        "phones",
    }
)
MASKED_KEYS = frozenset({"number", "cardnumber", "firstdigits"})
REDACTED = "***"


def redact_card_data(data):
    """Return a copy of the data without the payment credentials.

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

    :param value: The card number.
    :return: The masked value.
    :rtype: str
    """
    if not isinstance(value, str) or len(value) <= 4:
        return REDACTED
    return f"{REDACTED}{value[-4:]}"
