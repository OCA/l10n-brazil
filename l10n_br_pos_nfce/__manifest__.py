# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Pos Nfce",
    "summary": """
        NFC-E no Ponto de Venda""",
    "version": "14.0.1.1.4",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "maintainers": ["mileo", "lfdivino", "luismalta", "ygcarvalh", "felipezago"],
    "depends": [
        "l10n_br_pos",
        "l10n_br_account_nfe",
    ],
    "data": [
        "views/res_partner.xml",
        "views/pos_payment_method.xml",
        "views/pos_template.xml",
        "views/pos_config_view.xml",
    ],
    "demo": [
        "demo/l10n_br_pos_nfce.xml",
    ],
    "qweb": [
        "static/src/xml/Screens/ReceiptScreen/NfceOrderReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/NfceHeaderReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/NfceFooterReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/NfceFiscalInfoReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/NfceTotalsReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/NfcePaymentlineReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/NfceItemReceipt.xml",
        "static/src/xml/Screens/ReceiptScreen/ReceiptScreen.xml",
    ],
    "installable": True,
}
