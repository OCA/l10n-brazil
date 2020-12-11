# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'PIX no Ponto de Venda',
    'summary': """PIX no Ponto de Venda""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    "maintainers": ['mileo'],
    'development_status': 'Alpha',
    'website': 'https://github.com/oca/l10n-brazil',
    'depends': [
        'l10n_br_pix',
        'pos_qr_show',
        'pos_qr_payments',
        'point_of_sale',
        'pos_longpolling',
    ],
    'data': [
        'views/l10n_br_pix_cob.xml',
        'views/assets.xml',
    ],
    "qweb": ["static/src/xml/pos.xml"],
    "demo": [],
}
