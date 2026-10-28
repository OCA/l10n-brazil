# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    CANCELADO_DENTRO_PRAZO,
    CANCELADO_FORA_PRAZO,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)


@openupgrade.migrate()
def migrate(env, version):
    """Set the fiscal state of the documents cancelled at SEFAZ.

    _nfe_cancel() compared the cStat string with the CANCELADO_*_PRAZO
    lists using `==`, so it never wrote state_fiscal. Without it, the
    SPED guard of _before_document_back2draft() let a cancelled NF-e go
    back to draft and be resent with its consumed number and key, which
    SEFAZ rejects as a duplicate (cStat 204).
    """
    documents = env["l10n_br_fiscal.document"].search(
        [
            ("state_edoc", "=", SITUACAO_EDOC_CANCELADA),
            ("state_fiscal", "=", False),
            ("cancel_event_id.state", "=", "done"),
        ]
    )
    for document in documents:
        status_code = document.cancel_event_id.status_code
        if status_code in CANCELADO_FORA_PRAZO:
            document.state_fiscal = SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
        elif status_code in CANCELADO_DENTRO_PRAZO:
            document.state_fiscal = SITUACAO_FISCAL_CANCELADO
