# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven do catálogo de operações: entrega / futura / vfe."""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

CFOP_CASES = [
    ("fo_ef_remessa_revenda_line", "5117", "6117", None),
    ("fo_ef_compra_line", "1922", "2922", None),
    ("fo_ef_entrada_ind_line", "1116", "2116", None),
    ("fo_ef_entrada_com_line", "1117", "2117", None),
    ("fo_vfe_remessa_producao", "5904", "6904", None),
    ("fo_vfe_retorno_producao", "1904", "2904", None),
    ("fo_vfe_venda_producao", "5103", "6103", None),
    ("fo_vfe_venda_revenda", "5104", "6104", None),
]

RETURN_LINKS = [
    ("fo_entrega_futura_entrada_ind", "fo_devolucao_compras"),
    ("fo_vfe_remessa", "fo_vfe_retorno"),
    ("fo_vfe_venda", "fo_devolucao_venda"),
]

TAX_DEF_CASES = [
    ("fo_ef_remessa_revenda_line", {"IPI": "53", "PIS": "49"}, ["ICMS"], []),
    ("fo_ef_compra_line", {"ICMS": "90"}, ["PIS"], []),
    ("fo_ef_entrada_ind_line", {"PIS": "98", "COFINS": "98"}, [], []),
    ("fo_vfe_remessa_producao", {"PIS": "49", "COFINS": "49"}, ["ICMS"], []),
    ("fo_vfe_venda_producao", {"ICMS": "90"}, ["PIS"], ["ICMS"]),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestCatalogEntregaFuturaVfe(OperationCatalogCommon):
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
