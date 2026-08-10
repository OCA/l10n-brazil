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


def set_document_serie(document):
    # The fiscal event of the document requires a series, and the demo
    # documents only carry the series code.
    serie = document.env["l10n_br_fiscal.document.serie"].search(
        [
            ("document_type_id", "=", document.document_type_id.id),
            ("company_id", "=", document.company_id.id),
        ],
        limit=1,
    )
    if not serie:
        serie = serie.create(
            {
                "name": "NFS-e Nacional",
                "code": "1",
                "document_type_id": document.document_type_id.id,
                "company_id": document.company_id.id,
            }
        )
    document.document_serie_id = serie.id
