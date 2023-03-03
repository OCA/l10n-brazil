odoo.define("l10n_br_pos_nfce.NfceOrderReceipt", function (require) {
    "use strict";

    const OrderReceipt = require("point_of_sale.OrderReceipt");
    const Registries = require("point_of_sale.Registries");

    const NfceOrderReceipt = (OrderReceipt) =>
        class extends OrderReceipt {
            mounted() {
                this._generateQRCode();
            }

            /* Basic Getters */
            get currentOrder() {
                return this.receipt;
            }

            get currentCompany() {
                return this.currentOrder.company;
            }

            get currentCompanyAddress() {
                return this.currentCompany.address;
            }

            get documentKey() {
                return this.currentOrder.document_key;
            }

            /* Getters to QWeb */

            get companyCnpj() {
                return this.currentOrder.cnpj_cpf;
            }

            get companyAddress() {
                return `${this.currentCompanyAddress.street_name}, ${this.currentCompanyAddress.district}, ${this.currentCompanyAddress.city} - ESTADO`;
            }

            get companyLegalName() {
                return `${this.receipt.company.legal_name}`;
            }

            get totalOrderItemsLength() {
                return this.currentOrder.orderlines.length;
            }

            get totalOrderAmount() {
                return this.env.pos.format_currency(this.currentOrder.total_with_tax);
            }

            get totalOrderDiscount() {
                return this.env.pos.format_currency(this.currentOrder.total_discount);
            }

            get totalOrderToPaid() {
                return this.env.pos.format_currency(this.currentOrder.total_with_tax);
            }

            get orderChange() {
                return this.env.pos.format_currency(this.currentOrder.change);
            }

            get documentKeyFormatted() {
                return this.documentKey.replace(/(.{4})/g, "$1 ");
            }

            get urlConsulta() {
                return this.currentOrder.url_consulta;
            }

            get documentNumber() {
                return this.currentOrder.document_number;
            }

            get documentSerie() {
                return this.currentOrder.document_serie;
            }

            get documentDate() {
                return this.currentOrder.document_date_string;
            }

            get autorizationProtocol() {
                return this.currentOrder.authorization_protocol;
            }

            get authorizationDate() {
                return this.currentOrder.authorization_date_string;
            }

            get qrCode() {
                return this.currentOrder.qr_code;
            }

            async _generateQRCode() {
                // eslint-disable-next-line
                return await new QRCode(document.getElementById("footer__qrcode"), {
                    text: this.qrCode,
                    width: 275,
                    height: 275,
                    colorDark: "#000000",
                    colorLight: "#ffffff",
                    // eslint-disable-next-line
                    correctLevel: QRCode.CorrectLevel.M,
                });
            }
        };

    Registries.Component.extend(OrderReceipt, NfceOrderReceipt);
    OrderReceipt.template = "NfceOrderReceipt";

    return OrderReceipt;
});
