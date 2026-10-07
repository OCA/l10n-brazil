/** @odoo-module */

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";

class NfcePaymentlineReceipt extends PosComponent {
    setup() {
        super.setup();

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

NfcePaymentlineReceipt.template = "NfcePaymentlineReceipt";

Registries.Component.add(NfcePaymentlineReceipt);
