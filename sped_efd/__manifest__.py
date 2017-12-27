# -*- coding: utf-8 -*-

{
    'name': 'SPED EFD',
    'category': 'Fiscal',
    'version': '11.0.1.0.0',
    'author': 'Odoo Community Association (OCA), Ari Caldeira',
    'category': 'Base',
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
        'views/sped_efd_view.xml',
    ],
    'external_dependencies': {
        'python': [
            'pybrasil',
            'email_validator',
        ],
    }
}
