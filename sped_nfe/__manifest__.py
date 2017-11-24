# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

{
    'name': u'SPED - NF-e / NFC-e',
    'version': '10.0.1.0.0',
    'author': u'"Odoo Community Association (OCA), Ari Caldeira',
    'category': u'Base',
    'depends': [
        'l10n_br_base',
        'sped_imposto',
        'sped',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'data': [
        'views/sped_certificado_view.xml',
        'views/inherited_sped_empresa_view.xml',
        'views/inherited_sped_documento_emissao_nfe_view.xml',
        'views/inherited_sped_documento_emissao_nfce_view.xml',
        'views/sped_documento_carta_correcao_view.xml',
        'views/sped_consulta_dfe_view.xml',
    ],
    'external_dependencies': {
        'python': ['pybrasil', 'pysped', 'mako'],
    }
}
