odoo.define("l10n_br_pos_cfe.OrderFooterReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class OrderFooterReceipt extends PosComponent {
        mounted() {
            this.footerMountedEvent = new Event("footer-mounted");

            this._generateBarcode(this.getFormattedDocumentKey());
            this._generateQRCode();

            if (this.order.state_edoc === "cancelada") {
                this._generateBarcodeCancel(this.getFormattedDocumentKeyCancel());
                this._generateQRCodeCancel();
            }
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

        _generateBarcodeCancel(documentKey) {
            $("#satBarcodeCancel").JsBarcode(documentKey, {
                displayValue: false,
                height: 60,
                width: 1.5,
            });
        }

        async _generateQRCode() {
            const qrCode = document.getElementById("footer__qrcode");
            new MutationObserver(this.observerCallback.bind(this)).observe(qrCode, {
                attributes: true,
                subtree: true,
                attributeFilter: ["style"]
            });

            const start = Date.now();

            // eslint-disable-next-line
            await new QRCode(document.getElementById("footer__qrcode"), {
                text: this.getTextForQRCode(),
                width: 275,
                height: 275,
                colorDark: "#000000",
                colorLight: "#ffffff",
                // eslint-disable-next-line
                correctLevel: QRCode.CorrectLevel.L,
            });
            const end = Date.now();

            console.log(`Gerar QR Code - Tempo de Execução: ${end - start} ms`);
        }

        getFormattedDocumentKey() {
            return this.order.document_key.replace("CFe", "");
        }

        getFormattedDocumentKeyCancel() {
            return this.order.cancel_document_key.replace("CFe", "");
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

        async _generateQRCodeCancel() {
            const qrCodeCancel = document.getElementById("footer__qrcode-cancel");
            new MutationObserver(this.observerCallback.bind(this)).observe(qrCodeCancel, {
                attributes: true,
                subtree: true,
                attributeFilter: ["style"]
            });

            // eslint-disable-next-line
            return await new QRCode(qrCodeCancel, {
                text: this.getTextForQRCodeCancel(),
                width: 275,
                height: 275,
                colorDark: "#000000",
                colorLight: "#ffffff",
                // eslint-disable-next-line
                correctLevel: QRCode.CorrectLevel.L,
            });
        }

        getTextForQRCodeCancel() {
            const orderDate = this.order.cancel_date;
            const qrCodeSignature = this.order.cancel_qrcode_signature;
            const orderTotalAmount = this.order.total_with_tax;
            const cnpjCpf = this.order.cnpj_cpf || "";

            const str = "";

            const qrCodeDate = this.getQRCodeDate(orderDate);

            return str.concat(
                this.getFormattedDocumentKeyCancel(),
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

        observerCallback(mutationList, observer) {
            const self = this;
            _.each(mutationList, (mutation) => {
                const currEl = mutation.target;
                if (mutation.type == "attributes" &&
                    currEl.tagName === "IMG" &&
                    currEl.style.display === "block"
                ) {
                    window.dispatchEvent(self.footerMountedEvent);
                    observer.disconnect();
                }
            });
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

        get isCanceled() {
            return this.order.state_edoc === "cancelada";
        }

        get document_key_cancel() {
            return this.getFormattedDocumentKeyCancel().replace(/(.{4})/g, "$1 ");
        }

        get document_date_cancel() {
            return moment(this.order.cancel_date).format("DD/MM/YYYY HH:mm:ss");
        }
    }
    OrderFooterReceipt.template = "OrderFooterReceipt";

    Registries.Component.add(OrderFooterReceipt);

    return OrderFooterReceipt;
});
