# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Ponto de venda adaptado a legislação Brasileira",
    "version": "16.0.1.0.1",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "development_status": "Alpha",
    "maintainers": ["mileo", "lfdivino", "luismalta", "ygcarvalh"],
    "depends": [
        "l10n_br_fiscal",
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
        #   "pos_order_return",
    ],
    "data": [
        # security
        "security/l10n_br_pos_product_fiscal_map.xml",
        # data
        "data/l10n_br_fiscal_cfop_data.xml",
        # Views
        "views/l10n_br_pos_product_fiscal_map.xml",
        "views/pos_config_view.xml",
        "views/pos_order_view.xml",
        "views/product_template_view.xml",
        "views/res_company.xml",
        "views/pos_payment_method_view.xml",
        # TODO: Check this files after alpha version
        #   Report
        #   "views/point_of_sale_report.xml",
    ],
    "demo": [
        "demo/product_template_demo.xml",
        "demo/pos_payment_method_demo.xml",
        "demo/pos_config_demo.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "l10n_br_pos/static/lib/JsBarcode.js",
            "l10n_br_pos/static/lib/qrcode.js",
            "l10n_br_pos/static/src/js/util.esm.js",
            "l10n_br_pos/static/src/js/models.esm.js",
            "l10n_br_pos/static/src/js/Screens/PaymentScreen/PaymentScreen.esm.js",
            "l10n_br_pos/static/src/js/Screens/TicketScreen/TicketScreen.esm.js",
            "l10n_br_pos/static/src/xml/Screens/TicketScreen/TicketScreen.xml",
        ],
    },
    "installable": True,
    "external_dependencies": {
        "python": [
            "erpbrasil.base",
        ]
    },
}
