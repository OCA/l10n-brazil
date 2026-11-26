# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven: modalidades especiais de importação."""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

# (linha, CFOP resolvido para parceiro no exterior)
EXTERIOR_CASES = [
    ("fo_imp_co_line", "3949"),
    ("fo_adm_temp_line", "3930"),
    ("fo_reexp_temp_line", "7930"),
    ("fo_draw_imp_line", "3127"),
    ("fo_draw_exp_line", "7127"),
    ("fo_draw_dev_c_line", "7211"),
    ("fo_draw_dev_v_line", "3211"),
]

# (linha, cfop interno, cfop interestadual) - pernas nacionais da conta e ordem
NACIONAL_CASES = [
    ("fo_rem_co_imp_line", "5949", "6949"),
    ("fo_aq_co_line", "1949", "2949"),
]

# (linha, {grupo: cst}) - tratamento tributário
TAX_CASES = [
    # trading não toma o crédito de importação (é do adquirente)
    ("fo_imp_co_line", {"PIS": "70", "COFINS": "70"}),
    # adquirente toma os créditos de importação
    ("fo_aq_co_line", {"PIS": "50", "COFINS": "50"}),
    # remessa ao adquirente não é receita
    ("fo_rem_co_imp_line", {"PIS": "49", "COFINS": "49"}),
    # admissão temporária: suspensão total (entrada 72, saída 09)
    ("fo_adm_temp_line", {"ICMS": "50", "IPI": "05", "PIS": "72", "COFINS": "72"}),
    ("fo_reexp_temp_line", {"ICMS": "50", "IPI": "55", "PIS": "09", "COFINS": "09"}),
    # drawback suspensão
    ("fo_draw_imp_line", {"ICMS": "50", "IPI": "05", "PIS": "72", "COFINS": "72"}),
    ("fo_draw_exp_line", {"IPI": "55", "PIS": "49", "COFINS": "49"}),
]

RETURN_LINKS = [
    ("fo_admissao_temporaria", "fo_reexportacao_temporaria"),
    ("fo_drawback_importacao", "fo_drawback_dev_compra"),
    ("fo_drawback_exportacao", "fo_drawback_dev_venda"),
    ("fo_aquisicao_conta_ordem", "fo_devolucao_compras"),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestCatalogImportacaoEspeciais(OperationCatalogCommon):
    def test_cfop_exterior(self):
        """Operações de exterior resolvem o CFOP 3xxx/7xxx pelo parceiro."""
        for line_xmlid, cfop in EXTERIOR_CASES:
            with self.subTest(line=line_xmlid):
                line = self.env.ref(f"{M}.{line_xmlid}")
                self.assertEqual(self._cfop_code(line, self.partner_exterior), cfop)

    def test_cfop_nacional(self):
        """Pernas nacionais da conta e ordem (remessa e aquisição)."""
        for line_xmlid, internal, external in NACIONAL_CASES:
            with self.subTest(line=line_xmlid):
                self.assert_operation_cfops(f"{M}.{line_xmlid}", internal, external)

    def test_tax_definitions(self):
        for line_xmlid, csts in TAX_CASES:
            with self.subTest(line=line_xmlid):
                line = self.env.ref(f"{M}.{line_xmlid}")
                defs = {d.tax_group_id.name: d for d in line.tax_definition_ids}
                for group, cst in csts.items():
                    self.assertEqual(
                        defs[group].cst_id.code, cst, f"{line_xmlid}/{group}"
                    )

    def test_suspensao_ii_sem_cst(self):
        """II suspenso nas entradas de regime especial: definition no grupo II,
        sem CST (o II não possui CST no modelo brasileiro)."""
        for line_xmlid in ("fo_adm_temp_line", "fo_draw_imp_line"):
            with self.subTest(line=line_xmlid):
                line = self.env.ref(f"{M}.{line_xmlid}")
                defs = {d.tax_group_id.name: d for d in line.tax_definition_ids}
                self.assertIn("II", defs)
                self.assertFalse(defs["II"].is_taxed)
                self.assertFalse(defs["II"].cst_id)

    def test_return_links(self):
        for op, ret in RETURN_LINKS:
            with self.subTest(op=op):
                self.assert_return_link(f"{M}.{op}", f"{M}.{ret}")
