# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven do catálogo de operações: importação direta."""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

# (linha, CFOP de importação, {grupo: cst}, alíquota PIS, alíquota COFINS)
IMPORT_CASES = [
    ("fo_importacao_revenda", "3102", {"PIS": "50", "COFINS": "50"}),
    ("fo_importacao_industrializacao", "3101", {"PIS": "50", "COFINS": "50"}),
    ("fo_importacao_ativo", "3551", {"PIS": "50", "COFINS": "50"}),
    ("fo_importacao_uso_consumo", "3556", {"PIS": "70", "COFINS": "70"}),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestCatalogImportacao(OperationCatalogCommon):
    def test_cfop_importacao(self):
        """Parceiro no exterior resolve o CFOP 3xxx; a linha não tem CFOP
        nacional (importação não tem operação interna/interestadual)."""
        for line_xmlid, cfop, _csts in IMPORT_CASES:
            with self.subTest(line=line_xmlid):
                line = self.env.ref(f"{M}.{line_xmlid}")
                self.assertEqual(self._cfop_code(line, self.partner_exterior), cfop)
                self.assertFalse(line.cfop_internal_id)
                self.assertFalse(line.cfop_external_id)

    def test_pis_cofins_importacao(self):
        """PIS/COFINS-Importação (2,1% / 9,65%, Lei 10.865/2004) com o CST de
        creditabilidade por destinação (50 com crédito; 70 uso/consumo)."""
        for line_xmlid, _cfop, csts in IMPORT_CASES:
            with self.subTest(line=line_xmlid):
                line = self.env.ref(f"{M}.{line_xmlid}")
                defs = {d.tax_group_id.name: d for d in line.tax_definition_ids}
                for group, cst in csts.items():
                    self.assertEqual(defs[group].cst_id.code, cst)
                self.assertEqual(defs["PIS"].tax_id.percent_amount, 2.10)
                self.assertEqual(defs["COFINS"].tax_id.percent_amount, 9.65)
                # ICMS/IPI/II sem definition: resolvem pelo regulamento e NCM.
                self.assertNotIn("ICMS", defs)
                self.assertNotIn("IPI", defs)

    def test_operacao_e_retorno(self):
        """Operação aprovada, de compra, com devolução pela devolução de
        compras do core (que já tem os CFOPs 7xxx de exterior)."""
        op = self.env.ref(f"{M}.fo_importacao")
        self.assertEqual(op.state, "approved")
        self.assertEqual(op.fiscal_type, "purchase")
        self.assert_return_link(
            f"{M}.fo_importacao", "l10n_br_fiscal.fo_devolucao_compras"
        )
