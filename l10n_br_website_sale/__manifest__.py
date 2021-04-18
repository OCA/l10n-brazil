# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Website Sale',
    'summary': """
        Website sale localização brasileira.""",
    'version': '12.0.1.1.0',
    "development_status": "Alpha",
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-brazil',
    'depends': [
        'website_sale',
        'l10n_br_sale',
        'l10n_br_portal',
    ],
    'data': [
        'templates/portal_templates.xml',
        'views/assets.xml',
    ],
    'demo': [
    ],
}
