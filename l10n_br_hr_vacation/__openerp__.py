# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Employees vacation / Vacation Prevision',
    'summary': 'Employees vacation prevision',
    'version': '8.0.1.0.0',
    'category': 'Generic Modules',
    'description': """
    Module for vacation and prevision vacation
    """,
    'author': "KMEE, Odoo Community Association (OCA)",
    'website': 'http://www.kmee.com.br',
    'depends': [
        'hr_contract',
        'hr_holidays',
    ],
    'data': [
        'data/hr_holidays_data.xml',
        'views/hr_holidays_view.xml',
    ],
    'installable': True,
}
