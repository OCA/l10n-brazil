# Copyright 2026 Engenere
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os


def _load_mock(filename):
    """Load mock XML response from file."""
    mocks_dir = os.path.join(os.path.dirname(__file__), "mocks")
    filepath = os.path.join(mocks_dir, filename)
    with open(filepath, "rb") as f:
        return f.read()


# A realistic SOAP response for a successful query with multiple documents  # noqa: E501
response_sucesso_multiplos = _load_mock("response_sucesso_multiplos.xml")

# Response when no documents are found for the CNPJ
response_137 = _load_mock("response_137.xml")

# Response for rate-limiting / excessive consumption
response_656_with_nsu = _load_mock("response_656.xml")
