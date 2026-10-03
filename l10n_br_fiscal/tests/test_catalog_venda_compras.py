# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven do catálogo de operações: venda / compras."""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

CFOP_CASES = [
    ("fo_venda_ativo_line", "5551", "6551", None),
    ("fo_complementar_valor_producao", "5101", "6101", "7101"),
    ("fo_compras_servico_icms", "1126", "2126", None),
    ("fo_compras_servico_iss", "1128", "2128", None),
    ("fo_devolucao_compras_servico", "5210", "6210", None),
]

TAX_DEF_CASES = [
    (
        "fo_venda_ativo_line",
        {"ICMS": "41", "PIS": "08", "COFINS": "08"},
        [],
        ["ICMS", "PIS"],
    ),
    (
        "fo_complementar_icms_line",
        {"PIS": "08", "COFINS": "08"},
        ["ICMS"],
        ["PIS", "COFINS"],
    ),
]

ATTR_CASES = [
    ("fo_venda_ativo", "fiscal_type", "other"),
    ("fo_complementar_valor", "edoc_purpose", "2"),
    ("fo_complementar_valor", "fiscal_type", "sale"),
    ("fo_complementar_icms", "edoc_purpose", "2"),
    ("fo_complementar_icms", "fiscal_type", "other"),
    ("fo_compras_servico_iss", "tax_icms_or_issqn", "issqn"),
    ("fo_devolucao_compras_servico", "product_type", "09"),
    ("fo_devolucao_compras_servico", "fiscal_operation_id.code", "DVC"),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestCatalogVendaCompras(OperationCatalogCommon):
    def test_cfops(self):
        """CFOP resolvido por destino (interno/interestadual/exportação)."""
        for line, internal, external, export in CFOP_CASES:
            with self.subTest(line=line):
                self.assert_operation_cfops(f"{M}.{line}", internal, external, export)

    def test_tax_definitions(self):
        """CST por grupo, ausência de definition (default) e não incidência."""
        for line, csts, absent, not_taxed in TAX_DEF_CASES:
            with self.subTest(line=line):
                rec = self.env.ref(f"{M}.{line}")
                defs = {d.tax_group_id.name: d for d in rec.tax_definition_ids}
                for group, cst in csts.items():
                    self.assertEqual(defs[group].cst_id.code, cst, f"{line}/{group}")
                for group in absent:
                    self.assertNotIn(group, defs, f"{line}/{group}")
                for group in not_taxed:
                    self.assertFalse(defs[group].is_taxed, f"{line}/{group}")

    def test_attrs(self):
        """Atributos pontuais (finalidade de emissão, tipo fiscal, ISSQN...)."""
        for xmlid, path, expected in ATTR_CASES:
            with self.subTest(xmlid=xmlid, attr=path):
                value = self.env.ref(f"{M}.{xmlid}")
                for part in path.split("."):
                    value = getattr(value, part)
                self.assertEqual(value, expected)
