# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

{
    'name': u'SPED',
    'version': '10.0.1.0.0',
    'author': u'Odoo Community Association (OCA), Ari Caldeira',
    'category': u'Base',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'document',
        'mail',
        'decimal_precision',
        'product',
    ],
    'installable': True,
    'application': True,
    'data': [
        #
        # Valores padrão
        #
        'data/inherited_res_currency_data.xml',
        'data/inherited_decimal_precision_data.xml',
        'data/inherited_product_uom_category_data.xml',
        # 'data/inherited_product_uom_data.xml',
        'data/sped_pais_data.xml',
        'data/sped_estado_data.xml',
        'data/sped_municipio_data.xml',
        'data/sped_municipio_exterior_data.xml',

        'data/sped_aliquota_icms_proprio_data.xml',
        'data/sped_aliquota_icms_st_data.xml',
        'data/sped_aliquota_ipi_data.xml',
        'data/sped_aliquota_pis_cofins_data.xml',
        'data/sped_aliquota_simples_anexo_data.xml',
        'data/sped_aliquota_simples_teto_data.xml',
        'data/sped_aliquota_simples_aliquota_data.xml',

        'data/sped_unidade_data.xml',
        'data/sped_ncm_data.xml',
        'data/sped_cest_data.xml',
        'data/sped_cnae_data.xml',
        'data/sped_cfop_data.xml',
        'data/sped_cfop_equivalente_data.xml',
        'data/sped_servico_data.xml',

        #
        # Menus principais
        #
        'views/cadastro_view.xml',
        'views/sped_view.xml',

        #
        # Tabelas principais
        #
        'views/sped_protocolo_icms_proprio_view.xml',
        'views/sped_aliquota_icms_proprio_view.xml',
        'views/sped_protocolo_icms_st_view.xml',
        'views/sped_aliquota_icms_st_view.xml',
        'views/sped_aliquota_ipi_view.xml',
        'views/sped_aliquota_pis_cofins_view.xml',
        'views/sped_aliquota_simples_view.xml',

        'views/sped_cfop_view.xml',
        'views/sped_cest_view.xml',
        'views/sped_nbs_view.xml',
        'views/sped_ncm_view.xml',
        'views/sped_servico_view.xml',
        'views/sped_ibptax_view.xml',
        'views/sped_cnae_view.xml',

        'views/sped_pais_view.xml',
        'views/sped_estado_view.xml',
        'views/sped_municipio_view.xml',

        #
        # Módulo Cadastro: participantes, produtos etc.
        #
        'views/sped_empresa_view.xml',
        'views/sped_empresa_vincula_company_view.xml',

        'views/sped_participante_cliente_view.xml',
        'views/sped_participante_fornecedor_view.xml',
        'views/sped_participante_vincula_partner_view.xml',

        'views/sped_produto_produto_view.xml',
        'views/sped_unidade_produto_view.xml',

        'views/sped_produto_servico_view.xml',
        'views/sped_unidade_servico_view.xml',

        #
        # Parcelamentos e pagamentos
        #
        'views/sped_account_payment_term_line_view.xml',
        'views/sped_account_payment_term_view.xml',

        #
        # Fiscal
        #
        'views/sped_natureza_operacao_view.xml',
        'views/sped_veiculo_view.xml',

        'views/sped_operacao_item_view.xml',

        'views/sped_operacao_base_view.xml',

        'views/sped_operacao_emissao_nfe_view.xml',
        'views/sped_operacao_emissao_nfce_view.xml',
        #'views/sped_operacao_recebimento_nfe_view.xml',

        'views/sped_documento_item_declaracao_importacao_view.xml',
        'views/sped_documento_item_emissao_view.xml',

        'views/sped_documento_referenciado_view.xml',
        'views/sped_documento_pagamento_view.xml',

        'views/sped_documento_base_view.xml',

        'views/sped_documento_emissao_nfe_view.xml',
        'views/sped_documento_emissao_nfce_view.xml',
        # 'views/sped_documento_recebimento_nfe_view.xml',
    ],
    'external_dependencies': {
        'python': ['pybrasil'],
    }
}
