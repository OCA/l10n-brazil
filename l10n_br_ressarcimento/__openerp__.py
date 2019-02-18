# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Ressarcimento de contrato',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'maintainer': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'version': '8.0.0.0.1',
    'depends': [
        'hr_payroll',
    ],
    'data': [
        'data/contract_ressarcimento_email.xml',
        'security/ressarcimento_security.xml',
        'security/ir.model.access.csv',
        'views/contract_ressarcimento.xml',
    ],
    'demo': [
        # 'demo/hr_contract.xml',
        # 'demo/l10n_br_hr_payroll_rubricas.xml',
        # 'demo/l10n_br_hr_payroll_estruturas.xml',
    ],
    'installable': True,
    'auto_install': False,
}
