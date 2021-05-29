# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Ponto de venda adaptado a legislação Brasileira",
    "version": "12.0.1.0.0",
    "author": "KMEE, "
              "Odoo Community Association (OCA)",
    "website": "http://github.com/OCA/l10n-brazil",
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "depends": [
        'l10n_br_stock_account',
        'l10n_br_zip',
        # 'pos_pricelist',
        # 'pos_payment_term',
        # 'pos_order_picking_link',
        'stock_picking_invoice_link',
        'point_of_sale',
    ],
    # "external_dependencies": {
    #     "python": ['satcomum'],
    # },
    'data': [
        # "wizard/l10n_br_pos_order_return.xml",
        # "views/pos_template.xml",
        # "views/point_of_sale_view.xml",
        # "views/point_of_sale_report.xml",
        # "views/pos_order_line_view.xml",
        # "views/res_partner.xml",
        # "views/res_company.xml",
        # "views/account_journal_view.xml",
        # "wizard/sat_xml_periodic_export.xml",
        # "views/account_invoice_view.xml"
    ],
    "qweb": [
        # 'static/src/xml/pos.xml',
    ],
    "installable": True,
}
