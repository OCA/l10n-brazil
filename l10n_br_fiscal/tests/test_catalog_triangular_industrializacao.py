# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven do catálogo de operações: triangular / industrializacao."""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

CFOP_CASES = [
    ("fo_venda_ordem_line", "5102", "6102", None),
    ("fo_venda_ordem_compra_line", "1118", "2118", None),
    ("fo_faturamento_ordem_producao", "5118", "6118", None),
    ("fo_faturamento_ordem_revenda", "5119", "6119", None),
    ("fo_remessa_conta_ordem_line", "5923", "6923", None),
    ("fo_compra_ordem_destinatario_line", "1102", "2102", None),
    ("fo_rti_insumo", "5902", "6902", None),
    ("fo_rti_mo", "5124", "6124", None),
    ("fo_eri_insumo", "1902", "2902", None),
    ("fo_eri_mo", "1124", "2124", None),
    ("fo_rem_ind_co_line", "5924", "6924", None),
    ("fo_ent_ind_co_line", "1924", "2924", None),
]

RETURN_LINKS = [
    ("fo_venda_ordem", "fo_venda_ordem_dev"),
    ("fo_remessa_conta_ordem", "fo_conta_ordem_retorno"),
    ("fo_remessa_ind_conta_ordem", "fo_entrada_retorno_ind_conta_ordem"),
]

TAX_DEF_CASES = [
    (
        "fo_remessa_conta_ordem_line",
        {"ICMS": "41", "PIS": "49", "COFINS": "49"},
        [],
        ["ICMS"],
    ),
    ("fo_rti_insumo", {"ICMS": "50", "IPI": "55"}, [], []),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestCatalogTriangularIndustrializacao(OperationCatalogCommon):
    def test_cfops(self):
        """CFOP resolvido por destino (interno/interestadual/exportação)."""
        for line, internal, external, export in CFOP_CASES:
            with self.subTest(line=line):
                self.assert_operation_cfops(f"{M}.{line}", internal, external, export)

    def test_return_links(self):
        """Encadeamento remessa/retorno via return_fiscal_operation_id."""
        for op, ret in RETURN_LINKS:
            with self.subTest(op=op):
                self.assert_return_link(f"{M}.{op}", f"{M}.{ret}")

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

    def test_mo_industrializacao_tributada(self):
        """A cobrança da industrialização (5124) não tem definition: tributa
        pelo default (é a receita do industrializador)."""
        self.assertFalse(self.env.ref(f"{M}.fo_rti_mo").tax_definition_ids)
