# -*- coding: utf-8 -*-
# Copyright 2016 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Resource',
    'summary': """
        Sets the Brazilian calendar and helper methods for calculation of
        working days, leaves of resources in non business day and etc.
        """,
    'version': '10.0.1.0.0',
    'category': 'Hidden',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.odoobrasil.org.br',
    'depends': [
        'resource',
        'l10n_br_base',
    ],
    'external_dependencies': {
        'python': [
            'pybrasil'
        ],
    },
    'data': [
        'views/inherited_resource_calendar_view.xml',
        'views/inherited_resource_calendar_leaves_view.xml',
        'views/menu_resource_calendar.xml',
        'wizard/pybrasil_holiday_import.xml',
    ],
    'post_init_hook':
        'create_national_calendar',
}
