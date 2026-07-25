# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Testes data-driven do catálogo de operações fiscais.

As tabelas abaixo declaram, por família, as verificações de CFOP por destino,
encadeamento remessa/retorno e tratamento tributário (CST por grupo). Cada
linha de tabela vira um subTest, com a mesma cobertura dos testes por família.
"""

from odoo.tests import tagged

from .operation_catalog_common import OperationCatalogCommon

M = "l10n_br_fiscal"

# (linha, cfop interno, cfop interestadual, cfop exportação ou None)
CFOP_CASES = [
    # consignação mercantil (Ajuste SINIEF 02/93)
    ("fo_consig_rem_line", "5917", "6917", None),
    ("fo_consig_rem_reaj_line", "5917", "6917", None),
    ("fo_consig_fat_line", "5114", "6114", None),
    ("fo_consig_ret_line", "1918", "2918", None),
    ("fo_consig_devsimb_ent_line", "1919", "2919", None),
    ("fo_consig_ent_line", "1917", "2917", None),
    ("fo_consig_venda_line", "5115", "6115", None),
    ("fo_consig_dev_line", "5918", "6918", None),
    ("fo_consig_devsimb_line", "5919", "6919", None),
    # venda: ativo e complementares
    ("fo_venda_ativo_line", "5551", "6551", None),
    ("fo_complementar_valor_producao", "5101", "6101", "7101"),
    # compras e devolução para prestação de serviço
    ("fo_compras_servico_icms", "1126", "2126", None),
    ("fo_compras_servico_iss", "1128", "2128", None),
    ("fo_devolucao_compras_servico", "5210", "6210", None),
    # bonificação / brinde / doação / amostra
    ("fo_brinde_line", "5910", "6910", None),
    ("fo_doacao_line", "5910", "6910", None),
    ("fo_amostra_line", "5911", "6911", None),
    ("fo_ent_bonif_line", "1910", "2910", None),
    ("fo_ent_amostra_line", "1911", "2911", None),
    # venda à ordem / triangular
    ("fo_venda_ordem_line", "5102", "6102", None),
    ("fo_venda_ordem_compra_line", "1118", "2118", None),
    ("fo_faturamento_ordem_producao", "5118", "6118", None),
    ("fo_faturamento_ordem_revenda", "5119", "6119", None),
    ("fo_remessa_conta_ordem_line", "5923", "6923", None),
    ("fo_compra_ordem_destinatario_line", "1102", "2102", None),
    # comodato
    ("fo_remessa_comodato_line", "5908", "6908", None),
    ("fo_entrada_retorno_comodato_line", "1909", "2909", None),
    ("fo_entrada_comodato_line", "1908", "2908", None),
    ("fo_devolucao_comodato_line", "5909", "6909", None),
    # industrialização por encomenda
    ("fo_rti_insumo", "5902", "6902", None),
    ("fo_rti_mo", "5124", "6124", None),
    ("fo_eri_insumo", "1902", "2902", None),
    ("fo_eri_mo", "1124", "2124", None),
    ("fo_rem_ind_co_line", "5924", "6924", None),
    ("fo_ent_ind_co_line", "1924", "2924", None),
    # ativo imobilizado (uso fora / conserto)
    ("fo_remessa_ativo_uso_fora_line", "5554", "6554", None),
    ("fo_retorno_ativo_uso_fora_line", "1554", "2554", None),
    ("fo_remessa_ativo_conserto_line", "5915", "6915", None),
    ("fo_retorno_ativo_conserto_line", "1916", "2916", None),
    # demonstração / feira
    ("fo_remessa_demonstracao_line", "5912", "6912", None),
    ("fo_retorno_demonstracao_entrada_line", "1913", "2913", None),
    ("fo_retorno_demonstracao_saida_line", "5913", "6913", None),
    ("fo_entrada_demonstracao_line", "1912", "2912", None),
    ("fo_remessa_feira_line", "5914", "6914", None),
    # transferências entre filiais
    ("fo_transf_saida_producao", "5151", "6151", None),
    ("fo_transf_saida_revenda", "5152", "6152", None),
    ("fo_transf_saida_ativo", "5552", "6552", None),
    ("fo_transf_saida_uso", "5557", "6557", None),
    ("fo_transf_entrada_producao", "1151", "2151", None),
    ("fo_transf_entrada_revenda", "1152", "2152", None),
    ("fo_dev_transf_ent_ind", "1208", "2208", None),
    ("fo_dev_transf_sai_com", "5209", "6209", None),
    # comércio exterior (remessa com fim específico)
    ("fo_remessa_export_producao", "5501", "6501", None),
    ("fo_remessa_export_revenda", "5502", "6502", None),
    ("fo_retorno_remessa_export_line", "1501", "2501", None),
    # armazém geral / vasilhame
    ("fo_remessa_deposito_line", "5905", "6905", None),
    ("fo_retorno_deposito_line", "1906", "2906", None),
    ("fo_remessa_vasilhame_line", "5920", "6920", None),
    ("fo_retorno_vasilhame_line", "1921", "2921", None),
    ("fo_entrada_vasilhame_line", "1920", "2920", None),
    ("fo_devolucao_vasilhame_line", "5921", "6921", None),
    # entrega futura
    ("fo_ef_remessa_revenda_line", "5117", "6117", None),
    ("fo_ef_compra_line", "1922", "2922", None),
    ("fo_ef_entrada_ind_line", "1116", "2116", None),
    ("fo_ef_entrada_com_line", "1117", "2117", None),
    # venda fora do estabelecimento
    ("fo_vfe_remessa_producao", "5904", "6904", None),
    ("fo_vfe_retorno_producao", "1904", "2904", None),
    ("fo_vfe_venda_producao", "5103", "6103", None),
    ("fo_vfe_venda_revenda", "5104", "6104", None),
]

# (operação, operação de retorno)
RETURN_LINKS = [
    ("fo_consig_rem", "fo_consig_ret"),
    ("fo_consig_ent", "fo_consig_dev"),
    ("fo_consig_venda", "fo_devolucao_venda"),
    ("fo_brinde", "fo_ent_bonif"),
    ("fo_amostra", "fo_ent_amostra"),
    ("fo_venda_ordem", "fo_venda_ordem_dev"),
    ("fo_remessa_conta_ordem", "fo_conta_ordem_retorno"),
    ("fo_remessa_comodato", "fo_entrada_retorno_comodato"),
    ("fo_entrada_comodato", "fo_devolucao_comodato"),
    ("fo_remessa_ind_conta_ordem", "fo_entrada_retorno_ind_conta_ordem"),
    ("fo_remessa_ativo_uso_fora", "fo_retorno_ativo_uso_fora"),
    ("fo_remessa_demonstracao", "fo_retorno_demonstracao_entrada"),
    ("fo_entrada_demonstracao", "fo_retorno_demonstracao_saida"),
    ("fo_remessa_feira", "fo_retorno_feira"),
    ("fo_transferencia_saida", "fo_devolucao_transferencia_entrada"),
    ("fo_transferencia_entrada", "fo_devolucao_transferencia_saida"),
    ("fo_remessa_export", "fo_retorno_remessa_export"),
    ("fo_entrega_futura_entrada_ind", "fo_devolucao_compras"),
    ("fo_vfe_remessa", "fo_vfe_retorno"),
    ("fo_vfe_venda", "fo_devolucao_venda"),
]

# (linha, {grupo: CST esperado}, grupos SEM definition, grupos com is_taxed=False)
TAX_DEF_CASES = [
    # dissociação de fato gerador: PIS/COFINS na receita, ICMS na circulação
    ("fo_consig_rem_line", {"PIS": "49", "COFINS": "49"}, ["ICMS"], []),
    ("fo_consig_fat_line", {"ICMS": "90"}, ["PIS", "COFINS"], []),
    ("fo_venda_ativo_line", {"ICMS": "41", "PIS": "08", "COFINS": "08"}, [], ["ICMS", "PIS"]),
    ("fo_complementar_icms_line", {"PIS": "08", "COFINS": "08"}, ["ICMS"], ["PIS", "COFINS"]),
    ("fo_brinde_line", {"PIS": "08", "COFINS": "08"}, ["ICMS"], []),
    ("fo_amostra_line", {"ICMS": "40", "IPI": "52", "PIS": "08"}, [], []),
    ("fo_bonificacao_bonificacao", {"PIS": "08", "COFINS": "08"}, [], []),
    ("fo_remessa_conta_ordem_line", {"ICMS": "41", "PIS": "49", "COFINS": "49"}, [], ["ICMS"]),
    ("fo_remessa_comodato_line", {"ICMS": "41", "PIS": "08"}, [], ["ICMS"]),
    ("fo_rti_insumo", {"ICMS": "50", "IPI": "55"}, [], []),
    ("fo_remessa_ativo_uso_fora_line", {"ICMS": "41"}, [], ["ICMS"]),
    ("fo_remessa_demonstracao_line", {"ICMS": "50", "IPI": "55", "PIS": "49"}, [], []),
    ("fo_retorno_demonstracao_entrada_line", {"ICMS": "41"}, [], ["ICMS"]),
    ("fo_transf_saida_producao", {"PIS": "49", "COFINS": "49"}, ["ICMS"], []),
    ("fo_transf_saida_ativo", {"ICMS": "90"}, [], ["ICMS"]),
    ("fo_remessa_export_producao", {"ICMS": "50", "IPI": "55", "PIS": "49"}, [], []),
    ("fo_baixa_estoque_line", {"ICMS": "90", "PIS": "49"}, [], []),
    ("fo_ef_remessa_revenda_line", {"IPI": "53", "PIS": "49"}, ["ICMS"], []),
    ("fo_ef_compra_line", {"ICMS": "90"}, ["PIS"], []),
    ("fo_ef_entrada_ind_line", {"PIS": "98", "COFINS": "98"}, [], []),
    ("fo_vfe_remessa_producao", {"PIS": "49", "COFINS": "49"}, ["ICMS"], []),
    ("fo_vfe_venda_producao", {"ICMS": "90"}, ["PIS"], ["ICMS"]),
]

# (registro, atributo em notação de ponto, valor esperado)
ATTR_CASES = [
    ("fo_venda_ativo", "fiscal_type", "other"),
    ("fo_complementar_valor", "edoc_purpose", "2"),
    ("fo_complementar_valor", "fiscal_type", "sale"),
    ("fo_complementar_icms", "edoc_purpose", "2"),
    ("fo_complementar_icms", "fiscal_type", "other"),
    ("fo_compras_servico_iss", "tax_icms_or_issqn", "issqn"),
    ("fo_devolucao_compras_servico", "product_type", "09"),
    ("fo_devolucao_compras_servico", "fiscal_operation_id.code", "DVC"),
    ("fo_remessa_ativo_uso_fora_line", "product_type", "08"),
]


@tagged("post_install", "-at_install", "op_catalog")
class TestOperationCatalog(OperationCatalogCommon):
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

    def test_consignacao_operations_loaded(self):
        """As 9 operações da consignação carregam aprovadas."""
        codes = [
            "CONSIG_REM", "CONSIG_REM_REAJ", "CONSIG_FAT", "CONSIG_RET",
            "CONSIG_DEVSIMB_ENT", "CONSIG_ENT", "CONSIG_VENDA", "CONSIG_DEV",
            "CONSIG_DEVSIMB",
        ]
        ops = self.env["l10n_br_fiscal.operation"].search([("code", "in", codes)])
        self.assertEqual(len(ops), 9)
        self.assertTrue(all(op.state == "approved" for op in ops))

    def test_simbolicas_zeradas(self):
        """Devolução simbólica de consignação: todos os grupos zerados."""
        line = self.env.ref(f"{M}.fo_consig_devsimb_line")
        groups = {d.tax_group_id.name for d in line.tax_definition_ids}
        self.assertEqual(groups, {"ICMS", "IPI", "PIS", "COFINS"})
        for d in line.tax_definition_ids:
            self.assertEqual(d.tax_id.percent_amount, 0.0)

    def test_mo_industrializacao_tributada(self):
        """A cobrança da industrialização (5124) não tem definition: tributa
        pelo default (é a receita do industrializador)."""
        self.assertFalse(self.env.ref(f"{M}.fo_rti_mo").tax_definition_ids)

    def test_baixa_estoque_so_interna(self):
        """Baixa de estoque (5927) não tem CFOP interestadual: é sempre interna."""
        line = self.env.ref(f"{M}.fo_baixa_estoque_line")
        self.assertEqual(self._cfop_code(line, self.partner_interno), "5927")
        self.assertFalse(line.cfop_external_id)
