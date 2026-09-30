# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_fiscal.constants.fiscal import PROCESSADOR_OCA

from ..constants.nfse_nacional import PROVEDOR_NFSE_NACIONAL


def set_provedor_nacional(documents):
    # The demo companies are shared with other modules, so the demo data
    # keeps their municipal provider and the tests switch it here. The
    # processor is set too: only l10n_br_nfe demo data sets it on them.
    documents.company_id.write(
        {
            "processador_edoc": PROCESSADOR_OCA,
            "provedor_nfse": PROVEDOR_NFSE_NACIONAL,
        }
    )
