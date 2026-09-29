# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from ..constants.nfse_nacional import PROVEDOR_NFSE_NACIONAL


def set_provedor_nacional(documents):
    # The demo companies are shared with other modules, so the demo data
    # keeps their municipal provider and the tests switch it here.
    documents.company_id.write({"provedor_nfse": PROVEDOR_NFSE_NACIONAL})
