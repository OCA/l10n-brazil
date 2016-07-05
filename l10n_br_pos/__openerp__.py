# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

{
    "name": "Ponto de venda adaptado a legislação Brasileira",
    "version": "8.0.1.0.0",
    "author": "KMEE INFORMATICA LTDA, "
              "Odoo Community Association (OCA)",
    'website': 'http://odoo-brasil.org',
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "depends": [
        'l10n_br_base',
        'point_of_sale',
        'pos_pricelist',
        'pos_payment_term',
    ],
    'data': [
        "views/pos_template.xml",
        "views/point_of_sale_view.xml",
        "views/point_of_sale_report.xml",
        "views/res_company.xml",
        "views/account_journal_view.xml",
        "views/l10n_br_account_product_view.xml",
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
    "installable": True,
}
