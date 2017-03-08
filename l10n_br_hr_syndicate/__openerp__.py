# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization HR Syndicate',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'maintainer': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'version': '8.0.0.0.1',
    'depends': [
        'l10n_br_hr_payroll'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_br_hr_syndicate_form.xml',
        'views/l10n_br_hr_syndicate_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
}
