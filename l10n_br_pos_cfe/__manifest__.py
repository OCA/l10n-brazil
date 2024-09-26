# Copyright 2018 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Pos Cfe",
    "summary": """CF-e""",
    "version": "14.0.1.4.1",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Point Of Sale",
    "development_status": "Alpha",
    "maintainers": ["mileo", "lfdivino", "luismalta", "ygcarvalh"],
    "depends": [
        "point_of_sale",
        "l10n_br_pos",
    ],
    "external_dependencies": {
        "python": [
            "satcomum",
            "erpbrasil.base>=2.3.0",
        ],
    },
    "data": [
        # Views
        "views/pos_payment_method_view.xml",
        # Templates
        "views/pos_template.xml",
    ],
    "demo": [
        "demo/pos_config_demo.xml",
        "demo/pos_payment_method_demo.xml",
    ],
    "qweb": [
        "static/src/xml/Screens/ReceiptScreen/SatOrderReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/OrderRowReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/OrderHeaderReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/OrderSubtitleReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/OrderPaymentReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/OrderTotalsReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/OrderFooterReceipt.xml",
    ],
    "installable": True,
}
