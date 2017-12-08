# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

{
    'name': u'SPED',
    'category': 'Fiscal',
    'version': '10.0.1.0.0',
    'author': u'Odoo Community Association (OCA), Ari Caldeira',
    'category': u'Base',
    'license': 'AGPL-3',
    'depends': [
        'l10n_br_base',
        'sped_imposto',
        'document',
        'product',
    ],
    'installable': True,
    'application': True,
    'data': [
        'report/sped_documento_report.xml',
        #
        # Menus
        #
        'views/sped_view.xml',

        #
        # Fiscal
        #
        'views/sped_veiculo_view.xml',

        'views/inherited_sped_operacao_base_view.xml',

        'views/sped_documento_item_declaracao_importacao_view.xml',
        'views/sped_documento_item_rastreabilidade_view.xml',
        'views/sped_documento_item_base_view.xml',
        'views/sped_documento_item_emissao_view.xml',

        'views/sped_documento_referenciado_view.xml',
        'views/sped_documento_pagamento_view.xml',

        'views/sped_documento_subsequente_view.xml',

        'views/sped_documento_base_view.xml',

        'views/sped_documento_emissao_nfe_view.xml',
        'views/sped_documento_emissao_nfce_view.xml',
        'views/sped_documento_emissao_nfse_view.xml',

        'views/sped_documento_item_emissao_servico_view.xml',
        'views/sped_documento_item_recebimento_view.xml',
        'views/sped_documento_recebimento_nfe_view.xml',
        #
        # Grupos e permissões
        #
        'security/sped_documento_ir_rule.xml',
        'security/ir.model.access.csv',
        #
        # Dados de base
        #
        'wizard/sped_documento_exportar_xml.xml',
        'wizard/base_config_settings.xml',
    ],
    'demo': [
        'demo/sped_participante_demo.xml',
    ],
    'external_dependencies': {
        'python': [
            'pybrasil',
            'email_validator',
        ],
    }
}
