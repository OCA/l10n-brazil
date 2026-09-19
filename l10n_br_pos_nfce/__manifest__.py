# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Pos Nfce",
    "summary": """
        NFC-E no Ponto de Venda""",
    "version": "16.0.1.3.2",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "maintainers": ["mileo", "lfdivino", "luismalta", "ygcarvalh", "felipezago"],
    "depends": [
        "l10n_br_pos",
        "l10n_br_account_nfe",
        "l10n_br_nfe",
    ],
    "data": [
        "views/res_partner.xml",
        "views/pos_payment_method.xml",
        "views/pos_config_view.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "l10n_br_pos_nfce/static/src/js/Screens/PaymentScreen/PaymentScreen.esm.js",
            "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/ReceiptScreen.esm.js",
            "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceOrderReceipt.esm.js",
            "l10n_br_pos_nfce/static/src/css/ReceiptOrder.css",
            "l10n_br_pos_nfce/static/src/js/models.esm.js",
            "l10n_br_pos_nfce/static/src/js/Screens/OrderManagementScreen/ControlButtons/CancelOrderButton.esm.js",
            "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceHeaderReceipt.esm.js",
            "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceFooterReceipt.esm.js",
            "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceFiscalInfoReceipt.esm.js",
            "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceTotalsReceipt.esm.js",
            "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfcePaymentlineReceipt.esm.js",
            "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceItemReceipt.esm.js",
            "l10n_br_pos_nfce/static/src/js/utils.esm.js",
            "l10n_br_pos_nfce/static/src/js/nfe-xml.esm.js",
            "l10n_br_pos_nfce/static/src/lib/xmlbuilder2.min.js",
            "l10n_br_pos_nfce/static/src/xml/Screens/ReceiptScreen/NfceOrderReceipt.xml",
            "l10n_br_pos_nfce/static/src/xml/Screens/ReceiptScreen/NfceHeaderReceipt.xml",
            "l10n_br_pos_nfce/static/src/xml/Screens/ReceiptScreen/NfceFooterReceipt.xml",
            "l10n_br_pos_nfce/static/src/xml/Screens/ReceiptScreen/NfceFiscalInfoReceipt.xml",
            "l10n_br_pos_nfce/static/src/xml/Screens/ReceiptScreen/NfceTotalsReceipt.xml",
            "l10n_br_pos_nfce/static/src/xml/Screens/ReceiptScreen/NfcePaymentlineReceipt.xml",
            "l10n_br_pos_nfce/static/src/xml/Screens/ReceiptScreen/NfceItemReceipt.xml",
            "l10n_br_pos_nfce/static/src/xml/Screens/ReceiptScreen/ReceiptScreen.xml",
        ],
    },
    "demo": [
        "demo/l10n_br_pos_nfce.xml",
    ],
    "installable": True,
}
