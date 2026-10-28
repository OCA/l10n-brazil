# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    SITUACAO_EDOC_CANCELADA,
)
from odoo.addons.l10n_br_nfe.constants.nfe import NFE_CANCEL_STATE_FISCAL


def fill_cancel_state_fiscal(env):
    """Set the fiscal state of the NF-e cancelled at SEFAZ.

    _nfe_cancel() compared the cStat string with the CANCELADO_*_PRAZO
    lists using `==`, and the status query (cStat 101/151) never wrote it,
    so state_fiscal stayed empty. Without it, the SPED guard of
    _before_document_back2draft() let a cancelled NF-e go back to draft and
    be resent with its consumed number and key, which SEFAZ rejects as a
    duplicate (cStat 204).

    The cStat comes from the homologated cancel event or, when there is
    none (cancellation found by the status query), from the document.
    """
    documents = env["l10n_br_fiscal.document"].search(
        [
            ("state_edoc", "=", SITUACAO_EDOC_CANCELADA),
            ("state_fiscal", "=", False),
            ("document_type_id.code", "in", [MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE]),
        ]
    )
    for document in documents:
        event = document.cancel_event_id
        if event.state == "done":
            status_code = event.status_code
        else:
            status_code = document.status_code
        state_fiscal = NFE_CANCEL_STATE_FISCAL.get(status_code)
        if state_fiscal:
            document.state_fiscal = state_fiscal


@openupgrade.migrate()
def migrate(env, version):
    fill_cancel_state_fiscal(env)
