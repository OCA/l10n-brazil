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
        'l10n_br_base',
        'sped_imposto',
        'document',
        'product',
        'copy_views',
    ],
    'installable': True,
    'application': True,
    'data': [
        #
        # Menus
        #
        'views/sped_view.xml',

        #
        # Fiscal
        #
        'views/sped_veiculo_view.xml',

        'views/sped_documento_item_declaracao_importacao_view.xml',
        'views/sped_documento_item_base_view.xml',
        'views/sped_documento_item_emissao_view.xml',

        'views/sped_documento_referenciado_view.xml',
        'views/sped_documento_pagamento_view.xml',

        'views/sped_documento_base_view.xml',

        'views/sped_documento_emissao_nfe_view.xml',
        'views/sped_documento_emissao_nfce_view.xml',
        'views/sped_documento_emissao_nfse_view.xml',

        'views/sped_documento_item_emissao_servico_view.xml',
        # 'views/sped_documento_recebimento_nfe_view.xml',
    ],
    'external_dependencies': {
        'python': [
            'pybrasil',
            'email_validator',
        ],
    }
}
