# -*- coding: utf-8 -*-

{
    'name': u'SPED',
    'version': '1.0',
    'author': u'Ari Caldeira',
    'maintainer': u'Taŭga Tecnologia',
    'category': u'Base',
    'description': u'Módulo Fiscal Brasil - Odoo',
    'depends': [
        'base',
        'document',
        'mail',
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
    'data': [
        #
        # Valores padrão
        #

        ##
        ## Módulo Tabela
        ##
        #'data/sped_aliquota_icms_proprio_data.xml',
        #'data/sped_aliquota_icms_st_data.xml',
        #'data/sped_aliquota_ipi_data.xml',
        #'data/sped_aliquota_pis_cofins_data.xml',
        #'data/sped_aliquota_simples_anexo_data.xml',
        #'data/sped_aliquota_simples_teto_data.xml',
        #'data/sped_aliquota_simples_aliquota_data.xml',

        #'data/sped_cest_data.xml',
        #'data/sped_ncm_data.xml',
        ##'data/sped_ncm_cest_data.xml',
        #'data/sped_cnae_data.xml',
        #'data/sped_cfop_data.xml',
        #'data/sped_cfop_equivalente_data.xml',
        #'data/sped_servico_data.xml',

        #'data/sped_pais_data.xml',
        #'data/sped_estado_data.xml',
        #'data/sped_municipio_data.xml',
        #'data/sped_municipio_exterior_data.xml',

        ##
        ## Módulo Cadastro: participantes, produtos etc.
        ##
        #'data/cadastro_unidade_data.xml',

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

        #
        # Telas e menus
        #
        #'views/cadastro_unidade_area_view.xml',
        #'views/cadastro_unidade_comprimento_view.xml',
        #'views/cadastro_unidade_peso_view.xml',
        #'views/cadastro_unidade_tempo_view.xml',
        #'views/cadastro_unidade_unidade_view.xml',
        #'views/cadastro_unidade_volume_view.xml',
        'views/cadastro_unidade_produto_view.xml',
        'views/cadastro_unidade_servico_view.xml',

        'views/cadastro_produto_produto_view.xml',
        'views/cadastro_produto_servico_view.xml',

        'views/res_partner_empresa_view.xml',
        'views/res_users_usuario_view.xml',
        'views/res_partner_cliente_view.xml',
        'views/res_partner_fornecedor_view.xml',

        #
        # Grupos e unidades
        #
        #'cadastro/views/company_grupo_view.xml',
        #'cadastro/views/company_matriz_filial_view.xml',

        #
        # Clientes, Fornecedores, Transportadoras etc.
        #
        #'cadastro/views/partner_address_view.xml',
        #'cadastro/views/partner_cliente_view.xml',
        #'cadastro/views/partner_fornecedor_view.xml',
        #'cadastro/views/partner_funcionario_view.xml',
        #'cadastro/views/partner_usuario_view.xml',
        #'cadastro/views/partner_todos_view.xml',


        #
        # Fiscal
        #
        'views/sped_certificado_view.xml',
        'views/sped_natureza_operacao_view.xml',
        'views/sped_veiculo_view.xml',

        'views/sped_operacao_item_view.xml',
        'views/sped_operacao_emissao_nfe_view.xml',
        'views/sped_operacao_recebimento_nfe_view.xml',

        'views/sped_documento_item_emissao_view.xml',
        'views/sped_documento_emissao_nfe_view.xml',
        'views/sped_documento_recebimento_nfe_view.xml',
    ]
}
