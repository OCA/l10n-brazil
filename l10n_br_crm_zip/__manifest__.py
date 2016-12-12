# -*- coding: utf-8 -*-
# Copyright (C) 2011  Fabio Negrini                                           #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization CRM Zip',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'Fabio Negrini, Odoo Community Association (OCA)',
    'website': 'http://odoobrasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'l10n_br_zip',
        'l10n_br_crm',
    ],
    'data': [
        'views/crm_lead_view.xml',
        'views/crm_opportunity_view.xml',
    ],
    'test': [
        'test/crm_lead_zip.yml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
