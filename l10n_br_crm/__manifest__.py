# -*- coding: utf-8 -*-
# Copyright (C) 2011 - TODAY  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization CRM',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'l10n_br_base',
        'crm',
    ],
    'data': [
        'views/crm_lead_view.xml',
        'views/crm_opportunity_view.xml',
    ],
    'demo': [],
    'test': [
        'test/crm_lead.yml',
    ],
    'installable': True,
    'auto_install': True,
}
