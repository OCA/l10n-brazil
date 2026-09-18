/** @odoo-module **/

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";


class NfceFooterReceipt extends PosComponent {
    setup() {
        super.setup();

        this.order = this.props.receipt;
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

    get qrCodeUrl() {
    if (!this.order.qr_code) {
        return false;
    }

    return (
        "/report/barcode/?barcode_type=QR&value=" +
        encodeURIComponent(this.order.qr_code) +
        "&width=150&height=150"
    );
}

    get hasConsumer() {
        return this.order.customer_tax_id;
    }

    get notIssuedInContingency() {
        return this.order.authorization_protocol;
    }
}

NfceFooterReceipt.template = "NfceFooterReceipt";

Registries.Component.add(NfceFooterReceipt);

