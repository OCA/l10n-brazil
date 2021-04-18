# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Brazilian Localization Website Sale Delivery',
    'summary': """
        Implements Brazilian freight values for delivery.""",
    'version': '12.0.2.1.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'development_status': 'Alpha',
    'maintainers': ['DiegoParadeda'],
    'website': 'https://github.com/oca/l10n-brazil',
    'depends': [
        'website_sale_delivery',
        'l10n_br_delivery',
        'l10n_br_website_sale',
    ],
    'data': [
        'views/website_sale_delivery_templates.xml',
        'views/assets.xml'
    ],
    'demo': [
    ],
    'category': 'Localization',
    'installable': True,
}
