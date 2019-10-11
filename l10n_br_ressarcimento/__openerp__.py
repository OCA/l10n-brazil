# -*- coding: utf-8 -*-

{
    'name': 'Brazilian Ressarcimento de contrato',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'ABGF',
    'maintainer': 'ABGF',
    'website': 'http://www.abgf.gov.br',
    'version': '8.0.0.0.1',
    'depends': [
        'l10n_br_hr_payroll'
    ],
    'data': [
        'data/contract_ressarcimento_email.xml',
        'views/contract_ressarcimento.xml',
        'views/contract_ressarcimento_config.xml',
        'views/hr_contract.xml',
        'security/ressarcimento_security.xml',
        'security/ir.model.access.csv',

    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
