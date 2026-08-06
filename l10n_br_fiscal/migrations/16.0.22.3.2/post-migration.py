# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Corrige o `fiscal_type` da operacao fiscal de Transferencia.

A operacao `fo_transferencia` foi criada com `fiscal_type = "return_out"`
(devolucao de saida). Em `l10n_br_account/models/fiscal_operation.py` o
mapeamento `FISCAL_TYPE_INVOICE` traduz `return_out` para `out_refund`, entao a
transferencia geraria nota de credito de saida em vez de nota de saida.

O registro vive em `data/operation_data.xml`, que e carregado com
`noupdate="1"`: corrigir o XML resolve so para instalacoes novas, e por isso
este script existe.

Defensivo de proposito: so escreve se o valor ainda for o errado, para nao
desfazer ajuste manual de quem ja tiver corrigido na propria base.
"""

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    operation = env.ref("l10n_br_fiscal.fo_transferencia", raise_if_not_found=False)
    if not operation:
        return
    if operation.fiscal_type != "return_out":
        return
    operation.write({"fiscal_type": "other"})
    _logger.info(
        "l10n_br_fiscal: fo_transferencia teve fiscal_type corrigido de "
        "'return_out' para 'other'."
    )
