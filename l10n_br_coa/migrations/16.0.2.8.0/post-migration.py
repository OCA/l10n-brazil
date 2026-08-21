# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Saneamento das contas dos impostos dedutíveis de entrada.

Os impostos ``<Imposto> Entrada Dedutível`` eram criados com a conta de
dedução de receita (``6.1.1.2.xx <Imposto> s/ Vendas`` e ``(-) <Imposto>
Devolução``) na linha de repartição. Na entrada isso produz um espelho
decorativo: a fatura debita ``<Imposto> a Compensar`` e credita
``<Imposto> s/ Vendas``, sem tirar o imposto do custo da mercadoria.

O correto é a linha de repartição não ter conta, para o core cair na conta da
linha base (estoque, conta ponte ou despesa) - comportamento que IBS, CBS e IS
já tinham. As linhas de repartição de reembolso também passam a receber o
fator, que antes só era aplicado quando havia conta.

Atenção: contas customizadas manualmente nesses impostos são zeradas. Cada
alteração é registrada no log.
"""

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    taxes = env["account.tax"].search(
        [
            ("deductible", "=", True),
            ("type_tax_use", "=", "purchase"),
            "|",
            ("active", "=", True),
            ("active", "=", False),
        ]
    )
    for tax in taxes:
        repartition_lines = (
            tax.invoice_repartition_line_ids | tax.refund_repartition_line_ids
        ).filtered(lambda line: line.repartition_type == "tax")
        for line in repartition_lines:
            if line.account_id:
                _logger.info(
                    "l10n_br_coa: imposto %s (empresa %s): conta %s removida "
                    "da linha de repartição",
                    tax.display_name,
                    tax.company_id.display_name,
                    line.account_id.code,
                )
                line.account_id = False
            if line.factor_percent != -100:
                line.factor_percent = -100
