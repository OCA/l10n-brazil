# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

{
    'name': u'SPED - CF-E - MFE e SAT',
    'version': '10.0.1.0.0',
    'author': u'KMEE,Odoo Community Association (OCA)',
    'category': u'Fiscal',
    'depends': [
        'sped_nfe',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'data': [
        'views/pdv_config.xml',
        'views/pdv_impressora_config.xml',
        'views/sped_documento_emissao_cfe_view.xml',
        'views/sped_operacao_emissao_cfe_view.xml',
        'views/web_asset_backend_template.xml',
        'views/sped_documento_cfe_configuracao_view.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'external_dependencies': {
        'python': [
            'satcfe',
            'pybrasil',
        ],
    }
}
