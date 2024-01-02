# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Ponto de venda adaptado a legislação Brasileira",
    "version": "14.0.1.5.2",
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
        "point_of_sale",
        "pos_epson_printer",
    ],
    "data": [
        # security
        "security/l10n_br_pos_product_fiscal_map.xml",

        # Views
        "views/cfop_views.xml",
        "views/l10n_br_pos_product_fiscal_map.xml",
        "views/pos_config_view.xml",
        "views/pos_order_view.xml",
        "views/product_template_view.xml",
        "views/pos_payment_method_view.xml",
        "views/res_company.xml",

        # Templates
        "views/pos_template.xml",
    ],
    "demo": [
        "demo/product_template_demo.xml",
        "demo/pos_payment_method_demo.xml",
        "demo/pos_config_demo.xml",
        "demo/pos_cfop_data.xml"
    ],
    "qweb": [
        "static/src/xml/Screens/OrderManagementScreen/ControlButtons/CancelOrderButton.xml",
        "static/src/xml/Screens/OrderManagementScreen/OrderList.xml",
        "static/src/xml/Screens/OrderManagementScreen/OrderRow.xml",
    ],
    "installable": True,
    "external_dependencies": {
        "python": [
            "erpbrasil.base>=2.3.0",
        ]
    },
}
