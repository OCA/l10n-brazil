# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Substituição de Funcionários',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ABGF,Odoo Community Association (OCA)',
    'website': 'www.odoobrasil.org.br',
    'depends': [
        'hr',
        'l10n_br_base',
        'l10n_br_hr_holiday',
        'resource',
    ],
    'external_dependencies': {
        'python': ['pybrasil'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/hr_holidays_groups.xml',
        'views/hr_substituicao.xml',
        'views/hr_holidays.xml',
        'views/hr_department.xml',
    ],
    'installable': True,
}
