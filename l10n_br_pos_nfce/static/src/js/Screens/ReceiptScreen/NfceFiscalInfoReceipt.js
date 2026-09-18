/** @odoo-module */

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";

class NfceFiscalInfoReceipt extends PosComponent {
    setup() {
        super.setup();

        this.order = this.props.receipt;
    }

    get documentKeyFormatted() {
        if (!this.order.document_key) {
            return "";
        }

        return this.order.document_key.replace(/(.{4})/g, "$1 ");
    }

    get urlConsulta() {
        return this.order.url_consulta || "";
    }
}

NfceFiscalInfoReceipt.template = "NfceFiscalInfoReceipt";

Registries.Component.add(NfceFiscalInfoReceipt);