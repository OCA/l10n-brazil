# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven do catálogo de operações: comex / armazem."""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

CFOP_CASES = [
    ("fo_remessa_export_producao", "5501", "6501", None),
    ("fo_remessa_export_revenda", "5502", "6502", None),
    ("fo_retorno_remessa_export_line", "1501", "2501", None),
    ("fo_remessa_deposito_line", "5905", "6905", None),
    ("fo_retorno_deposito_line", "1906", "2906", None),
    ("fo_remessa_vasilhame_line", "5920", "6920", None),
    ("fo_retorno_vasilhame_line", "1921", "2921", None),
    ("fo_entrada_vasilhame_line", "1920", "2920", None),
    ("fo_devolucao_vasilhame_line", "5921", "6921", None),
]

RETURN_LINKS = [
    ("fo_remessa_export", "fo_retorno_remessa_export"),
]

TAX_DEF_CASES = [
    ("fo_remessa_export_producao", {"ICMS": "50", "IPI": "55", "PIS": "49"}, [], []),
    ("fo_baixa_estoque_line", {"ICMS": "90", "PIS": "49"}, [], []),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestCatalogComexArmazem(OperationCatalogCommon):
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

    def test_baixa_estoque_so_interna(self):
        """Baixa de estoque (5927) não tem CFOP interestadual: é sempre interna."""
        line = self.env.ref(f"{M}.fo_baixa_estoque_line")
        self.assertEqual(self._cfop_code(line, self.partner_interno), "5927")
        self.assertFalse(line.cfop_external_id)
