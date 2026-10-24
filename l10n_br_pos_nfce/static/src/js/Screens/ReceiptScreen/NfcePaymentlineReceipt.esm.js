import {Component} from "@odoo/owl";

export class NfcePaymentlineReceipt extends Component {
    static template = "l10n_br_pos_nfce.NfcePaymentlineReceipt";
    static props = {payment: Object};

    setup() {
        this.payment = this.props.payment;
    }

    get paymentName() {
        return this.payment.name || "";
    }

    get paymentAmount() {
        return (this.payment.amount || 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }
}
