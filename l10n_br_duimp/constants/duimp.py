# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

"""Constants for the Portal Único Siscomex DUIMP REST API integration.

References:

- https://docs.portalunico.siscomex.gov.br/api/plat/ (authentication)
- https://api-docs.portalunico.siscomex.gov.br/swagger/duimp.html
  (Consulta aos Dados da Duimp)
- https://github.com/samuelfac/portalunico.siscomex.gov.br (community
  OpenAPI-generated client used to validate the JSON field names)
"""

DUIMP_ENVIRONMENT_VALIDATION = "validation"
DUIMP_ENVIRONMENT_PRODUCTION = "production"

DUIMP_ENVIRONMENTS = {
    DUIMP_ENVIRONMENT_VALIDATION: "https://val.portalunico.siscomex.gov.br",
    DUIMP_ENVIRONMENT_PRODUCTION: "https://portalunico.siscomex.gov.br",
}

DUIMP_ENVIRONMENT_SELECTION = [
    (DUIMP_ENVIRONMENT_VALIDATION, "Company Validation"),
    (DUIMP_ENVIRONMENT_PRODUCTION, "Production"),
]

DUIMP_AUTH_PATH = "/portal/api/autenticar"

# Base path of the "Intervenientes Privados" DUIMP microservice (a
# different backend than the /portal/api/autenticar SSO gateway above).
# Confirmed by probing https://val.portalunico.siscomex.gov.br directly:
# requests without this prefix are rejected by the edge server with a
# bare Apache 403 (the route is never routed to the DUIMP application),
# while requests with it reach the app and return its own JSON
# "Usuário não autenticado" (DIMP-ER8990) error when no token is sent.
DUIMP_API_PATH_PREFIX = "/duimp-api/api/ext/duimp"

# The version segment is mandatory on the live API: a general-data/items
# request without it 404s at the application level (RESTEASY003210,
# "no matching route"), it is not silently resolved to the latest
# version. When the caller does not know the version yet, default to 1
# (every DUIMP starts at version 1 when first registered).
DUIMP_DEFAULT_VERSION = 1

DUIMP_ROLE_TYPE_DEFAULT = "IMPEXP"

DUIMP_DOCUMENT_TYPE_CODE = "55"

# "tipo" values of the header-level "tributos.tributosCalculados" list
# that are mapped into l10n_br_fiscal.document.line tax fields, keyed by
# the field prefix used on l10n_br_fiscal.document.line.mixin (ii_*,
# ipi_*, pis_*, cofins_*). ICMS is intentionally absent: it is a state
# (not federal) tax and this federal DUIMP service never returns it.
DUIMP_TAX_FIELD_PREFIX = {
    "II": "ii",
    "IPI": "ipi",
    "PIS": "pis",
    "COFINS": "cofins",
}

# Default lookback window (in days) used to prefill the search wizard's
# date range when listing the DUIMPs registered for the company.
DUIMP_SEARCH_DEFAULT_DAYS = 60

# The Portal Único rejects a new /portal/api/autenticar call if the same
# user authenticated less than 60 seconds ago (HTTP 422 PLAT-ER2033,
# "O token gerado deve ser reaproveitado"), confirmed live: a second
# "Search DUIMP" click right after the first one raised it. The token
# must be cached and reused across calls instead of re-authenticating
# every time; this TTL (in seconds) bounds how long a cached token is
# trusted before authenticating again.
DUIMP_TOKEN_CACHE_SECONDS = 300
