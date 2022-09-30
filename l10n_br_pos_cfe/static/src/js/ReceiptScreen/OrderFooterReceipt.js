odoo.define("l10n_br_pos_cfe.OrderFooterReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class OrderFooterReceipt extends PosComponent {
        mounted() {
            this._generateBarcode(this.getFormattedDocumentKey());
            this._generateQRCode();
        }

        get order() {
            return this.props.order;
        }

        _generateBarcode(documentKey) {
            $("#satBarcode").JsBarcode(documentKey, {
                displayValue: false,
                height: 60,
                width: 1.5,
            });
        }

        async _generateQRCode() {
            // eslint-disable-next-line
            return await new QRCode(document.getElementById("footer__qrcode"), {
                text: this.getTextForQRCode(),
                width: 275,
                height: 275,
                colorDark: "#000000",
                colorLight: "#ffffff",
                // eslint-disable-next-line
                correctLevel: QRCode.CorrectLevel.L,
            });
        }

        getFormattedDocumentKey() {
            return this.order.document_key.replace("CFe", "");
        }

        getTextForQRCode() {
            const orderDate = this.order.authorization_date;
            const qrCodeSignature = this.order.document_qrcode_signature;
            const orderTotalAmount = this.order.total_with_tax;
            const cnpjCpf = this.order.cnpj_cpf || "";

            const str = "";

            const qrCodeDate = this.getQRCodeDate(orderDate);

            return str.concat(
                this.getFormattedDocumentKey(),
                "|",
                qrCodeDate,
                "|",
                orderTotalAmount,
                "|",
                cnpjCpf,
                "|",
                qrCodeSignature
            );
        }

        getQRCodeDate(authorization_date) {
            return authorization_date
                .replaceAll("-", "")
                .replaceAll(":", "")
                .replaceAll("T", "");
        }

        // Getters //

        get satNumber() {
            return this.order.document_serie;
        }

        get document_key() {
            return this.getFormattedDocumentKey().replace(/(.{4})/g, "$1 ");
        }

        get document_date() {
            return moment(this.order.authorization_date).format("DD/MM/YYYY HH:mm:ss");
        }
    }
    OrderFooterReceipt.template = "OrderFooterReceipt";

    Registries.Component.add(OrderFooterReceipt);

    return OrderFooterReceipt;
});
