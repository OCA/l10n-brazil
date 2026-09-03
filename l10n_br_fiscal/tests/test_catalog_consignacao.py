# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven do catálogo de operações: consignacao."""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

CFOP_CASES = [
    ("fo_consig_rem_line", "5917", "6917", None),
    ("fo_consig_rem_reaj_line", "5917", "6917", None),
    ("fo_consig_fat_line", "5114", "6114", None),
    ("fo_consig_ret_line", "1918", "2918", None),
    ("fo_consig_devsimb_ent_line", "1919", "2919", None),
    ("fo_consig_ent_line", "1917", "2917", None),
    ("fo_consig_venda_line", "5115", "6115", None),
    ("fo_consig_dev_line", "5918", "6918", None),
    ("fo_consig_devsimb_line", "5919", "6919", None),
]

RETURN_LINKS = [
    ("fo_consig_rem", "fo_consig_ret"),
    ("fo_consig_ent", "fo_consig_dev"),
    ("fo_consig_venda", "fo_devolucao_venda"),
]

TAX_DEF_CASES = [
    ("fo_consig_rem_line", {"PIS": "49", "COFINS": "49"}, ["ICMS"], []),
    ("fo_consig_fat_line", {"ICMS": "90"}, ["PIS", "COFINS"], []),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestCatalogConsignacao(OperationCatalogCommon):
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

    def test_operations_loaded(self):
        """As 9 operações da família carregam aprovadas."""
        codes = [
            "CONSIG_REM",
            "CONSIG_REM_REAJ",
            "CONSIG_FAT",
            "CONSIG_RET",
            "CONSIG_DEVSIMB_ENT",
            "CONSIG_ENT",
            "CONSIG_VENDA",
            "CONSIG_DEV",
            "CONSIG_DEVSIMB",
        ]
        ops = self.env["l10n_br_fiscal.operation"].search([("code", "in", codes)])
        self.assertEqual(len(ops), 9)
        self.assertTrue(all(op.state == "approved" for op in ops))

    def test_simbolicas_zeradas(self):
        """Devolução simbólica (Mecânica B): todos os grupos zerados."""
        line = self.env.ref(f"{M}.fo_consig_devsimb_line")
        groups = {d.tax_group_id.name for d in line.tax_definition_ids}
        self.assertEqual(groups, {"ICMS", "IPI", "PIS", "COFINS"})
        for d in line.tax_definition_ids:
            self.assertEqual(d.tax_id.percent_amount, 0.0)
