# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Base',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Odoo Community Association (OCA), Akretion',
    'website': 'http://odoo-brasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'base',
        'mail',
        'base_setup',
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

        'data/res_country_data.xml',
        'data/res_country_state_data.xml',

        'data/sped_pais_data.xml',
        'data/sped_estado_data.xml',
        'data/sped_municipio_data.xml',
        'data/sped_municipio_exterior_data.xml',

        'data/sped_cnae_data.xml',

#        'views/res_bank_view.xml',

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

        'views/sped_cnae_view.xml',

        #
        # Módulo Cadastro: participantes, produtos etc.
        #
        'views/sped_participante_base_view.xml',
        'views/sped_participante_cliente_view.xml',
        'views/sped_participante_fornecedor_view.xml',
        'views/sped_participante_vincula_partner_view.xml',
        'views/sped_empresa.xml',

        #
        # Parcelamentos e pagamentos; bancos e contas bancárias
        #
        'views/sped_account_payment_term_line_view.xml',
        'views/sped_account_payment_term_view.xml',

        #
        # Parcelamentos e pagamentos; bancos e contas bancárias
        #
        'views/sped_account_payment_term_line_view.xml',
        'views/sped_account_payment_term_view.xml',

#        'security/ir.model.access.csv',
    ],
    'demo': [
        #        'demo/l10n_br_base_demo.xml',
        #        'demo/res_partner_demo.xml',
    ],
    'test': [
        #        'test/base_inscr_est_valid.yml',
        #        'test/base_inscr_est_invalid.yml',
        #        'test/res_partner_test.yml',
        #        'test/res_company_test.yml',
    ],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        'python': [
            'pybrasil',
            'email_validator',
            'num2words',
        ],
    }
}
