# -*- coding: utf-8 -*-

{
    'name': 'Brazilian Ressarcimento Account',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'ABGF',
    'maintainer': 'ABGF',
    'website': 'http://www.abgf.gov.br',
    'version': '8.0.0.0.1',
    'depends': [
        'hr_payroll',
        'l10n_br_hr_payroll',
        'l10n_br_ressarcimento',
    ],
    'data': [
        'views/contract_ressarcimento.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
