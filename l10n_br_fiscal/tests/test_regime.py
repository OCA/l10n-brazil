# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

MODULE = "l10n_br_fiscal"
SN_GROUP = "ICMS - Simples Nacional"


@tagged("post_install", "-at_install", "op_catalog")
class TestRegime(OperationCatalogCommon):
    """O catálogo é neutro de regime: a empresa é o único ponto de configuração.

    A mesma fiscal.operation resolve CST (regime normal) ou CSOSN (Simples)
    conforme o tax_framework da empresa — trocar a empresa de regime não exige
    reconfigurar nenhuma operação.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_sn = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.company_lp = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        # Parceiro demo com IE: o ind_ie_dest é computado (sem IE vira
        # não-contribuinte), então é preciso um contribuinte real.
        cls.partner_contribuinte = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.product_00 = cls.env["product.product"].create(
            {
                "name": "Produto Teste Regime",
                "fiscal_type": "00",
                "tax_icms_or_issqn": "icms",
            }
        )

    def _line_for(self, op_xmlid, company):
        operation = self.env.ref(op_xmlid)
        return operation.line_definition(
            company, self.partner_contribuinte, self.product_00
        )

    def test_simples_casa_linha_csosn(self):
        """Empresa SN casa a linha irmã SN (CSOSN 400); regime normal, a genérica."""
        op = f"{MODULE}.fo_consig_rem"
        line_sn = self._line_for(op, self.company_sn)
        self.assertEqual(line_sn.company_tax_framework, "1")
        defs = {d.tax_group_id.name: d for d in line_sn.tax_definition_ids}
        self.assertEqual(defs[SN_GROUP].cst_id.code, "400")
        self.assertNotIn("ICMS", defs)

        line_lp = self._line_for(op, self.company_lp)
        self.assertFalse(line_lp.company_tax_framework)
        defs_lp = {d.tax_group_id.name: d for d in line_lp.tax_definition_ids}
        # na remessa em consignação o ICMS destaca pelo default (sem definition)
        self.assertNotIn("ICMS", defs_lp)
        self.assertEqual(defs_lp["PIS"].cst_id.code, "49")

    def test_troca_de_regime_sem_reconfigurar(self):
        """Simples -> Presumido -> Real trocando só o cadastro da empresa."""
        company = self.company_lp
        op = f"{MODULE}.fo_consig_rem"

        # Presumido (regime normal): linha genérica com CST.
        self.assertFalse(self._line_for(op, company).company_tax_framework)

        # Empresa "entra" no Simples: muda só o tax_framework no cadastro.
        company.tax_framework = "1"
        self.assertEqual(self._line_for(op, company).company_tax_framework, "1")

        # Sai do Simples para o Presumido: volta à linha genérica. Nenhuma
        # operação foi reconfigurada em nenhum momento.
        company.tax_framework = "3"
        self.assertFalse(self._line_for(op, company).company_tax_framework)

        # Presumido -> Real: muda só o profit_calculation no cadastro; a
        # linha da operação é a mesma (a diferença de PIS/COFINS vem do
        # default da empresa, não do catálogo).
        line_before = self._line_for(op, company)
        company.profit_calculation = "real"
        line_after = self._line_for(op, company)
        self.assertEqual(line_before, line_after)
        company.profit_calculation = "presumed"

    def test_excesso_sublimite_usa_cst(self):
        """Empresa framework=2 (excesso de sublimite) recolhe ICMS fora do DAS:
        cai na linha genérica com CST, não na linha SN."""
        company = self.company_lp
        company.tax_framework = "2"
        line = self._line_for(f"{MODULE}.fo_consig_rem", company)
        self.assertFalse(line.company_tax_framework)
        company.tax_framework = "3"

    def test_receita_sn_nao_fixa_csosn(self):
        """Linhas de receita (faturamento de consignação) na variante SN não
        fixam ICMS/CSOSN — herdam a tributação SN default da empresa."""
        line_sn = self.env.ref(f"{MODULE}.fo_consig_fat_line_sn")
        groups = {d.tax_group_id.name for d in line_sn.tax_definition_ids}
        self.assertNotIn("ICMS", groups)
        self.assertNotIn(SN_GROUP, groups)

    def test_simbolica_sn_usa_900(self):
        """Simbólicas/ajustes na variante SN usam CSOSN 900."""
        line = self.env.ref(f"{MODULE}.fo_consig_devsimb_line_sn")
        defs = {d.tax_group_id.name: d for d in line.tax_definition_ids}
        self.assertEqual(defs[SN_GROUP].cst_id.code, "900")
