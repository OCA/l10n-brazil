import {Component} from "@odoo/owl";

export class NfceTotalsReceipt extends Component {
    static template = "l10n_br_pos_nfce.NfceTotalsReceipt";
    static props = {receipt: Object};

    setup() {
        this.order = this.props.receipt;
    }

    get totalOrderItemsLength() {
        return this.order.orderlines.length;
    }

    get totalOrderAmount() {
        return (this.order.amount_total || 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    get totalOrderDiscount() {
        return (this.order.total_discount || 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }
}
