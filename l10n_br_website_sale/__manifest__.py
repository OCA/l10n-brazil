# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Website Sale',
    'summary': """
        Website sale localização brasileira.""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'web',
        'website_sale',
        'l10n_br_sale',
    ],
    'data': [
        'templates/portal_templates.xml',
        'views/assets.xml',
    ],
    'demo': [
    ],
}
