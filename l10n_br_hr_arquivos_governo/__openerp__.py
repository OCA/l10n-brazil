# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'l10n br hr Arquivos Governo',
    'version': '8.0.0.0.1',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'maintainer': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'depends': [
        'document',
        'l10n_br_hr_payroll',
        'l10n_br_account',
    ],
    'external_dependencies': {
        'python': ['pybrasil'],
    },
    'data': [
        'security/hr_payslip.xml',
        'views/hr_payslip.xml',
        'wizards/wizard_l10n_br_hr_caged.xml',
    ],
}
