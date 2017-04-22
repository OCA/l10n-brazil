# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright 2017 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#

{
    'name': 'Brazilian Localisation Base',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Odoo Community Association (OCA), Akretion, Taŭga, KMEE',
    'website': 'http://odoo-brasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'base',
        'mail',
        'decimal_precision',
        'copy_views',
    ],
    'data': [
        #
        # Valores padrão
        #
        'data/inherited_res_currency_simbolo_data.xml',
        'data/inherited_res_currency_data.xml',
        'data/inherited_decimal_precision_data.xml',

        'data/inherited_res_country_data.xml',
        'data/inherited_res_country_state_data.xml',

        'data/sped_pais_data.xml',
        'data/sped_estado_data.xml',
        'data/sped_municipio_data.xml',
        'data/sped_municipio_exterior_data.xml',

        #
        # Menus principais
        #
        'views/l10n_br_base_menus_view.xml',

        #
        # Cadastros de localização
        #
        'views/sped_pais_view.xml',
        'views/sped_estado_view.xml',
        'views/sped_municipio_view.xml',

        #
        # Módulo Cadastro: participantes, produtos etc.
        #
        'views/sped_participante_base_view.xml',
        'views/sped_participante_cliente_view.xml',
        'views/sped_participante_fornecedor_view.xml',
        'views/sped_participante_vincula_partner_view.xml',
        'views/sped_empresa_view.xml',

        #
        # Parcelamentos e pagamentos; bancos e contas bancárias
        #
        'views/sped_account_payment_term_line_view.xml',
        'views/sped_account_payment_term_view.xml',

        #
        # Grupos e permissões
        #
        'security/inherited_res_groups_data.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/sped_empresa_demo.xml',
    ],
    'test': [
       'test/sped_participante_test.yml',
    ],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        'python': [
            'pybrasil',
            'email_validator',
        ],
    }
}
