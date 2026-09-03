# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven do catálogo de operações: bonificacao / comodato."""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

CFOP_CASES = [
    ("fo_brinde_line", "5910", "6910", None),
    ("fo_doacao_line", "5910", "6910", None),
    ("fo_amostra_line", "5911", "6911", None),
    ("fo_ent_bonif_line", "1910", "2910", None),
    ("fo_ent_amostra_line", "1911", "2911", None),
    ("fo_remessa_comodato_line", "5908", "6908", None),
    ("fo_entrada_retorno_comodato_line", "1909", "2909", None),
    ("fo_entrada_comodato_line", "1908", "2908", None),
    ("fo_devolucao_comodato_line", "5909", "6909", None),
]

RETURN_LINKS = [
    ("fo_brinde", "fo_ent_bonif"),
    ("fo_amostra", "fo_ent_amostra"),
    ("fo_remessa_comodato", "fo_entrada_retorno_comodato"),
    ("fo_entrada_comodato", "fo_devolucao_comodato"),
]

TAX_DEF_CASES = [
    ("fo_brinde_line", {"PIS": "08", "COFINS": "08"}, ["ICMS"], []),
    ("fo_amostra_line", {"ICMS": "40", "IPI": "52", "PIS": "08"}, [], []),
    ("fo_bonificacao_bonificacao", {"PIS": "08", "COFINS": "08"}, [], []),
    ("fo_remessa_comodato_line", {"ICMS": "41", "PIS": "08"}, [], ["ICMS"]),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestCatalogBonificacaoComodato(OperationCatalogCommon):
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
