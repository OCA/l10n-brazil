# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Employees vacation / Vacation Prevision',
    'summary': 'Employees vacation prevision',
    'version': '8.0.1.0.0',
    'category': 'Generic Modules',
    'website': 'http://www.kmee.com.br',
    'author': "KMEE, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    'depends': [
        'l10n_br_hr_holiday',
        'l10n_br_hr_payroll',
    ],
    'data': [
        'data/hr_holidays_data.xml',
        'security/ir.model.access.csv',
        'views/hr_holidays_view.xml',
        'views/hr_vacation_control_view.xml',
        'views/hr_vacation_resume.xml',
        'views/menuitem_hr_holidays_vacation.xml',
        'views/res_config_view.xml',
    ],
    'installable': True,
}
