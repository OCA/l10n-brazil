# -*- coding: utf-8 -*-
# Copyright 2017 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sped Imposto',
    'category': 'Fiscal',
    'summary': """
        Definições de impostos brasileiros""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Odoo Community Association (OCA)',
    'website': 'www.odoobrasil.org.br',
    'external_dependencies': {
        'python': [
            'pybrasil'
        ],
    },
    'depends': [
        'l10n_br_base',
        'product',
    ],
    'data': [
        'views/product_category.xml',

        #
        # Grupos e permissões
        #
        'security/inherited_res_groups_data.xml',
        'security/ir.model.access.csv',
        'security/sped_operacao_ir_rule.xml',
        'security/sped_operacao_subsequente.xml',

        #
        # Valores padrão
        #
        'data/sped_aliquota_icms_proprio_data.xml',
        'data/sped_aliquota_icms_st_data.xml',
        'data/sped_aliquota_ipi_data.xml',
        'data/sped_aliquota_pis_cofins_data.xml',
        'data/sped_aliquota_simples_anexo_data.xml',
        'data/sped_aliquota_simples_teto_data.xml',
        'data/sped_aliquota_simples_aliquota_data.xml',

        'data/sped_ncm_data.xml',
        'data/sped_cest_data.xml',
        'data/sped_cnae_data.xml',
        'data/sped_cfop_data.xml',
        'data/sped_cfop_equivalente_data.xml',
        'data/sped_servico_data.xml',

        'data/sped_protocolo_data.xml',
        'data/sped_data.yml',

        #
        # Cadastros
        #
        'views/inherited_sped_empresa_view.xml',
        'views/inherited_sped_participante_base_view.xml',
        'views/inherited_sped_produto_produto_view.xml',
        'views/inherited_sped_produto_servico_view.xml',

        #
        # Tabelas principais
        #
        'views/sped_view.xml',
        'views/sped_aliquota_icms_proprio_view.xml',
        'views/sped_aliquota_icms_st_view.xml',
        'views/sped_aliquota_ipi_view.xml',
        'views/sped_aliquota_pis_cofins_view.xml',
        'views/sped_aliquota_simples_view.xml',

        'views/sped_protocolo_icms_proprio_view.xml',
        'views/sped_protocolo_icms_st_view.xml',

        'views/sped_cfop_view.xml',
        'views/sped_cest_view.xml',
        'views/sped_nbs_view.xml',
        'views/sped_ncm_view.xml',
        'views/sped_servico_view.xml',
        'views/sped_ibptax_view.xml',
        'views/sped_cnae_view.xml',

        'views/sped_natureza_operacao_view.xml',
        'views/sped_operacao_subsequente.xml',
        'views/sped_operacao_item_view.xml',
        'views/sped_operacao_base_view.xml',
        #
        # Emissão de documento
        #
        'views/sped_operacao_emissao_nfe_view.xml',
        'views/sped_operacao_emissao_nfse_view.xml',
        'views/sped_operacao_emissao_nfce_view.xml',
        'views/sped_operacao_recebimento_nfe_view.xml',
    ],
    'demo': [
        'demo/sped_produto_demo.xml',
        'demo/sped_natureza_operacao_data.xml',
        'demo/sped_operacao_simples_data.xml',
        'demo/sped_operacao_presumido_data.xml',
        'demo/sped_empresa.xml',
    ],
}
