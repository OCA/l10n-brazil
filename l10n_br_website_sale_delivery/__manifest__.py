# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Website Sale Delivery',
    'summary': """
        Implements Brazilian freight values for delivery.""",
    'version': '12.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/l10n-brazil',
    'depends': [
        'website_sale_delivery',
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
