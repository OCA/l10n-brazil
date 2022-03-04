# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Ponto de venda adaptado a legislação Brasileira",
    "version": "12.0.1.0.0",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "depends": [
        "queue_job",
        "l10n_br_stock_account",
        "l10n_br_zip",
        "l10n_br_base",
        # 'pos_payment_term',
        # 'pos_order_picking_link',
        # 'stock_picking_invoice_link',
        "point_of_sale",
        "pos_order_show_list",
        "pos_hamburger_menu",
        "pos_show_order_hamburger_menu",
        "pos_order_return",
    ],
    "external_dependencies": {
        "python": ['satcomum'],
    },
    "data": [
        "data/operation_line_data.xml",
        "data/l10n_br_fiscal.tax.csv",
        "data/icms_tax_definition_data.xml",
        "security/l10n_br_pos_product_fiscal_map.xml",
        # "data/l10n_br_fiscal_cfop_data.xml",
        "data/account_journal_data.xml",
        # "data/pos_config_data.xml",
        "views/l10n_br_pos_product_fiscal_map.xml",
        "views/pos_config_view.xml",
        "views/pos_order_view.xml",
        "views/product_template_view.xml",
        # "wizard/l10n_br_pos_order_return.xml",
        # "wizard/sat_xml_periodic_export.xml",
        # "views/res_partner.xml",
        # "views/account_invoice_view.xml"
        # "views/res_company.xml",
        # "views/pos_order_line_view.xml",
        "views/account_journal_view.xml",
        # "views/point_of_sale_report.xml",
        "views/pos_template.xml",
    ],
    "demo": [
        "demo/product_template_demo.xml",
        "demo/account_journal_demo.xml",
        "demo/pos_config_demo.xml",
    ],
    "qweb": [
        "static/src/xml/pos.xml",
    ],
    "installable": True,
}
