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
    "maintainers": ["mileo", "lfdivino", "luismalta", "ygcarvalh", "felipezago",'OtavioAndretta'],
    "depends": [
        "l10n_br_pos",
        "l10n_br_account_nfe",
        "l10n_br_nfe",
    ],
    "data": [
        "views/res_partner.xml",
        "views/pos_payment_method.xml",
        # "views/pos_template.xml", #nao declaramos os assets assim mais no odoo16, agora é direto no manifest
        "views/pos_config_view.xml",
    ],

    "assets": {
    "point_of_sale.assets": [
        "l10n_br_pos_nfce/static/src/js/Screens/PaymentScreen/PaymentScreen.js",
        "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/ReceiptScreen.js",
        "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceOrderReceipt.js",
        "l10n_br_pos_nfce/static/src/css/ReceiptOrder.css",
        "l10n_br_pos_nfce/static/src/js/models.js",
        "l10n_br_pos_nfce/static/src/js/Screens/OrderManagementScreen/ControlButtons/CancelOrderButton.js",
        "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceHeaderReceipt.js",
        "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceFooterReceipt.js",
        "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceFiscalInfoReceipt.js",
        "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceTotalsReceipt.js",
        "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfcePaymentlineReceipt.js",
        "l10n_br_pos_nfce/static/src/js/Screens/ReceiptScreen/NfceItemReceipt.js",
        "l10n_br_pos_nfce/static/src/js/utils.js",
        "l10n_br_pos_nfce/static/src/js/nfe-xml.js",
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
    # "qweb": [   #nao se usa mais essa declaracao no Odoo16
    #     "static/src/xml/Screens/ReceiptScreen/NfceOrderReceipt.xml",
    #     "static/src/xml/Screens/ReceiptScreen/NfceHeaderReceipt.xml",
    #     "static/src/xml/Screens/ReceiptScreen/NfceFooterReceipt.xml",
    #     "static/src/xml/Screens/ReceiptScreen/NfceFiscalInfoReceipt.xml",
    #     "static/src/xml/Screens/ReceiptScreen/NfceTotalsReceipt.xml",
    #     "static/src/xml/Screens/ReceiptScreen/NfcePaymentlineReceipt.xml",
    #     "static/src/xml/Screens/ReceiptScreen/NfceItemReceipt.xml",
    #     # "static/src/xml/Screens/ReceiptScreen/ReceiptScreen.xml",
    # ],
    "installable": True,
}
