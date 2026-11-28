# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Devolve as contas de repartição dos impostos dedutiveis ao estado de fabrica.

A migration do PR de creditabilidade esvazia a conta da linha de repartição dos
impostos dedutiveis de **entrada**, e isso nao volta atras ao trocar de branch:
e dado, nao codigo. Para medir a localizacao limpa e preciso repor as contas de
deducao de receita (`6.1.1.2.xx <Imposto> s/ Vendas`) que o plano entrega.

    docker compose -f devel.yaml run --rm -T odoo \\
        odoo shell -d devel --log-level=warn --no-http \\
        < l10n_br_creditability_test_suite/scripts/restore_stock_baseline.py

Le o mapeamento do proprio plano (`l10n_br_coa.account.tax.group.account.template`),
entao nao ha codigo de conta escrito a mao aqui.
"""

# Script para `odoo shell`, nao um modulo carregado pelo Odoo:
# `env` e injetado pelo shell e a saida impressa e o proprio produto.
# flake8: noqa: F821
# pylint: disable=print-used

restored = 0
for company in env["res.company"].search([("country_id.code", "=", "BR")]):
    templates = env["l10n_br_coa.account.tax.group.account.template"].search([])
    if not templates:
        continue
    for template in templates:
        taxes = env["account.tax"].search(
            [
                ("company_id", "=", company.id),
                ("tax_group_id", "=", template.tax_group_id.id),
                ("deductible", "=", True),
                ("type_tax_use", "=", "purchase"),
                "|",
                ("active", "=", True),
                ("active", "=", False),
            ]
        )
        if not taxes:
            continue
        for source, lines_field in (
            (template.ded_account_id, "invoice_repartition_line_ids"),
            (template.ded_refund_account_id, "refund_repartition_line_ids"),
        ):
            if not source:
                continue
            account = env["account.account"].search(
                [("code", "=", source.code), ("company_id", "=", company.id)], limit=1
            )
            if not account:
                continue
            for tax in taxes:
                lines = tax[lines_field].filtered(
                    lambda line: line.repartition_type == "tax"
                )
                for line in lines:
                    if line.account_id != account:
                        line.account_id = account
                        restored += 1
                        print(
                            "  %-14s %-30s %s -> %s"
                            % (
                                company.name[:14],
                                tax.name,
                                lines_field.split("_")[0],
                                account.code,
                            )
                        )

env.cr.commit()
print()
print("linhas de repartição restauradas:", restored)
