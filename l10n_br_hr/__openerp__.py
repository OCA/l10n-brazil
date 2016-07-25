# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name' : 'Brazilian Localization HR',
    'description' : """
Brazilian Localization HR with informations refered to the national context of HR""",
    'category' : 'Localization',
    'author' : 'KMEE',
    'maintainer': 'KMEE',
    'website' : 'http://www.kmee.com.br',
    'version' : '0.1',
    'depends' : ['hr','l10n_br_base'],
    'data': [
             'data/l10n_br_hr.cbo.csv',
             'security/ir.model.access.csv',
             'view/l10n_br_hr_cbo_view.xml',
             'view/hr_employee_view.xml',
             'view/hr_job_view.xml',
             ],
    'test': [],
    'installable': True,
    'images': [],
    'auto_install': False,
    'license': 'AGPL-3',
}
