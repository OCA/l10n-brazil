# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Portal',
    'summary': """
        Campos Brasileiros no Portal""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://odoo-brasil.org',
    'depends': [
        'portal',
        'l10n_br_zip',
    ],
    'data': [
        'views/assets.xml',

        'views/portal_templates.xml',
    ],
    'demo': [
    ],
    'auto_install': True,
}
