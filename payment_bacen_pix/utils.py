# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# A Pix charge carries no card, but it carries the name and the document of the
# payer, and the log of a gateway has no reason to keep them.
DROPPED_KEYS = frozenset({"cpf", "cnpj", "nome", "email", "logradouro", "cep"})
REDACTED = "***"


def redact_personal_data(data):
    """Return a copy of the data without the personal data of the payer.

    :param data: The payload or the response to redact.
    :return: The redacted copy, safe to log.
    """
    if isinstance(data, dict):
        return {
            key: REDACTED
            if str(key).replace("_", "").lower() in DROPPED_KEYS
            else redact_personal_data(value)
            for key, value in data.items()
        }
    elif isinstance(data, list | tuple):
        return [redact_personal_data(item) for item in data]
    return data
