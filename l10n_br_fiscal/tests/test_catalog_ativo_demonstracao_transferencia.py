# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven do catálogo de operações: ativo / demonstracao / transferencia."""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

CFOP_CASES = [
    ("fo_remessa_ativo_uso_fora_line", "5554", "6554", None),
    ("fo_retorno_ativo_uso_fora_line", "1554", "2554", None),
    ("fo_remessa_ativo_conserto_line", "5915", "6915", None),
    ("fo_retorno_ativo_conserto_line", "1916", "2916", None),
    ("fo_remessa_demonstracao_line", "5912", "6912", None),
    ("fo_retorno_demonstracao_entrada_line", "1913", "2913", None),
    ("fo_retorno_demonstracao_saida_line", "5913", "6913", None),
    ("fo_entrada_demonstracao_line", "1912", "2912", None),
    ("fo_remessa_feira_line", "5914", "6914", None),
    ("fo_transf_saida_producao", "5151", "6151", None),
    ("fo_transf_saida_revenda", "5152", "6152", None),
    ("fo_transf_saida_ativo", "5552", "6552", None),
    ("fo_transf_saida_uso", "5557", "6557", None),
    ("fo_transf_entrada_producao", "1151", "2151", None),
    ("fo_transf_entrada_revenda", "1152", "2152", None),
    ("fo_dev_transf_ent_ind", "1208", "2208", None),
    ("fo_dev_transf_sai_com", "5209", "6209", None),
]

RETURN_LINKS = [
    ("fo_remessa_ativo_uso_fora", "fo_retorno_ativo_uso_fora"),
    ("fo_remessa_demonstracao", "fo_retorno_demonstracao_entrada"),
    ("fo_entrada_demonstracao", "fo_retorno_demonstracao_saida"),
    ("fo_remessa_feira", "fo_retorno_feira"),
    ("fo_transferencia_saida", "fo_devolucao_transferencia_entrada"),
    ("fo_transferencia_entrada", "fo_devolucao_transferencia_saida"),
]

TAX_DEF_CASES = [
    ("fo_remessa_ativo_uso_fora_line", {"ICMS": "41"}, [], ["ICMS"]),
    ("fo_remessa_demonstracao_line", {"ICMS": "50", "IPI": "55", "PIS": "49"}, [], []),
    ("fo_retorno_demonstracao_entrada_line", {"ICMS": "41"}, [], ["ICMS"]),
    ("fo_transf_saida_producao", {"PIS": "49", "COFINS": "49"}, ["ICMS"], []),
    ("fo_transf_saida_ativo", {"ICMS": "90"}, [], ["ICMS"]),
]

ATTR_CASES = [
    ("fo_remessa_ativo_uso_fora_line", "product_type", "08"),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestCatalogAtivoDemonstracaoTransferencia(OperationCatalogCommon):
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

    def test_attrs(self):
        """Atributos pontuais (finalidade de emissão, tipo fiscal, ISSQN...)."""
        for xmlid, path, expected in ATTR_CASES:
            with self.subTest(xmlid=xmlid, attr=path):
                value = self.env.ref(f"{M}.{xmlid}")
                for part in path.split("."):
                    value = getattr(value, part)
                self.assertEqual(value, expected)
