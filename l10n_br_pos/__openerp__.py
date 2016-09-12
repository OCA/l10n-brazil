# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Ponto de venda adaptado a legislação Brasileira",
    "version": "8.0.1.0.0",
    "author": "KMEE INFORMATICA LTDA, "
              "Odoo Community Association (OCA)",
    'website': 'http://odoo-brasil.org',
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "depends": [
        'l10n_br_sale_stock',
        'point_of_sale',
        'pos_pricelist',
        'pos_payment_term',
        'nfe_attach',
        'pos_order_picking_link'
    ],
    'data': [
        "wizard/l10n_br_pos_order_return.xml",
        "views/pos_template.xml",
        "views/point_of_sale_view.xml",
        "views/point_of_sale_report.xml",
        "views/res_company.xml",
        "views/account_journal_view.xml",
        "wizard/sat_xml_periodic_export.xml",
        "views/account_invoice_view.xml"
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
    "installable": True,
}
