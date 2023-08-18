odoo.define("l10n_br_pos_nfce.NfceFooterReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class NfceFooterReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this.order = this.props.receipt;
        }

        mounted() {
            this._generateQRCode();
        }

        get documentNumber() {
            return this.order.document_number;
        }

        get documentSerie() {
            return this.order.document_serie;
        }

        get documentDate() {
            return this.order.document_date_string;
        }

        get autorizationProtocol() {
            return this.order.authorization_protocol;
        }

        get authorizationDate() {
            return this.order.authorization_date_string;
        }

        get qrCodeText() {
            return this.order.qr_code;
        }

        get hasConsumer() {
            return this.order.customer_tax_id;
        }

        get notIssuedInContingency() {
            return this.order.authorization_protocol;
        }

        async _generateQRCode() {
            // eslint-disable-next-line
            return await new QRCode(document.getElementById("footerQrCode"), {
                text: this.qrCodeText,
                width: 150,
                height: 150,
                colorDark: "#000000",
                colorLight: "#ffffff",
                // eslint-disable-next-line
                correctLevel: QRCode.CorrectLevel.M,
            });
        }
    }
    NfceFooterReceipt.template = "NfceFooterReceipt";

    Registries.Component.add(NfceFooterReceipt);

    return {NfceFooterReceipt};
});
