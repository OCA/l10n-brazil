import {Component} from "@odoo/owl";

export class NfceFiscalInfoReceipt extends Component {
    static template = "l10n_br_pos_nfce.NfceFiscalInfoReceipt";
    static props = {receipt: Object};

    setup() {
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
