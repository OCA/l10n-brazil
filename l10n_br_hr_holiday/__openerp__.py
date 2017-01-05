# -*- coding: utf-8 -*-
# Copyright 2016 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Hr Holiday',
    'description': """
        Registro de ocorrencias de faltas/atrasos dos funcionarios""",
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE INFORMATICA LTDA',
    'website': 'www.kmee.com.br',
    'depends': [
        'hr_holidays',
        'l10n_br_resource',
    ],
    'data': [
        'views/hr_holidays.xml',
        'views/hr_holidays_status.xml',
        'data/hr_holidays_status_data.xml',
        'security/hr_holidays_status.xml',
    ],
    'demo': [
    ],
}
