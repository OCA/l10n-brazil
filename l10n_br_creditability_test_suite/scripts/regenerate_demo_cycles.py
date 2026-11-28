# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Regera os ciclos de demonstracao numa base ja instalada.

Os ciclos sao dados de demonstracao do modulo: instalar com demo ligado ja os
cria. Este script serve para regerar sem reinstalar - depois de mexer numa
configuracao de imposto, por exemplo, para ver o efeito no razao.

    docker compose -f devel.yaml run --rm -T odoo \\
        odoo shell -d devel --log-level=warn --no-http \\
        < l10n_br_creditability_test_suite/scripts/regenerate_demo_cycles.py

Idempotente por referencia: se o ciclo ja existe, ele e reaproveitado. Para
gerar um novo, apague a fatura antiga ou mude a `ref`.
"""

# Script para `odoo shell`, nao um modulo carregado pelo Odoo:
# `env` e injetado pelo shell e a saida impressa e o proprio produto.
# flake8: noqa: F821
# pylint: disable=print-used

demo = env["l10n_br.creditability.demo"]

for label, method in (
    ("1A revenda OFF", "generate_case_1a"),
    ("1B revenda ON", "generate_case_1b"),
    ("2A uso e consumo OFF", "generate_case_2a"),
    ("2B uso e consumo ON", "generate_case_2b"),
):
    bill = getattr(demo, method)()
    if not bill:
        print(f"  {label:<16} nao gerado (ver o log)")
        continue
    lines = bill.invoice_line_ids.filtered(lambda ln: ln.display_type == "product")
    layers = env["stock.valuation.layer"].search(
        [("product_id", "in", lines.product_id.ids)]
    )
    print()
    print("=" * 78)
    print(f"  {bill.ref}")
    print(f"  fatura {bill.name} ({bill.state}) | CFOP {lines.cfop_id.code}")
    print("=" * 78)
    for line in bill.line_ids:
        conta = f"{line.account_id.code} {line.account_id.name}"[:44]
        print(f"    {conta:<44} D {line.debit:9.2f}  C {line.credit:9.2f}")
    print("  camadas de valoracao do produto:")
    for layer in layers:
        origem = "correcao da fatura" if layer.stock_valuation_layer_id else "entrada"
        print(
            f"    SVL[{layer.id}] value={layer.value:9.2f}  "
            f"remaining={layer.remaining_value:9.2f}  {origem}"
        )

env.cr.commit()
print()
print("gravado.")
