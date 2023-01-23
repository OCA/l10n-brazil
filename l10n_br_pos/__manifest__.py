# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Ponto de venda adaptado a legislação Brasileira",
    "version": "14.0.1.0.0",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "development_status": "Alpha",
    "maintainers": ["mileo", "sadamo", "gabrielcardoso21", "lfdivino"],
    "depends": [
        "l10n_br_account",
        "l10n_br_stock",
        "l10n_br_zip",
        "l10n_br_base",
        "point_of_sale",
        # TODO: Check this files after alpha version
        #   "queue_job",
        #   "l10n_br_stock_account",
        #   'pos_payment_term',
        #   'pos_order_picking_link',
        #   'stock_picking_invoice_link',
        #   "pos_order_show_list",
        #   "pos_hamburger_menu",
        #   "pos_show_order_hamburger_menu",
        #   "pos_order_return",
    ],
    "external_dependencies": {
        "python": ["satcomum"],
    },
    "data": [
        # security
        "security/l10n_br_pos_product_fiscal_map.xml",
        # data
        "data/l10n_br_fiscal_cfop_data.xml",
        "data/pos_payment_method_data.xml",
        "data/pos_config_data.xml",
        # Views
        "views/l10n_br_pos_product_fiscal_map.xml",
        "views/pos_config_view.xml",
        "views/pos_order_view.xml",
        "views/product_template_view.xml",
        "views/res_company.xml",
        "views/pos_payment_method_view.xml",
        # Templates
        "views/pos_template.xml",
        # TODO: Check this files after alpha version
        #   "views/account_invoice_view.xml"
        #   "views/pos_order_line_view.xml",
        #   Wizards
        #   "wizard/l10n_br_pos_order_return.xml",
        #   "wizard/sat_xml_periodic_export.xml",
        #   Report
        #   "views/point_of_sale_report.xml",
    ],
    "demo": [
        "demo/product_template_demo.xml",
        "demo/pos_payment_method_demo.xml",
        "demo/pos_config_demo.xml",
    ],
    "qweb": [
        # "static/src/xml/pos.xml",
        "static/src/xml/Screens/OrderManagementScreen/ControlButtons/CancelOrderButton.xml",
    ],
    "installable": True,
}
