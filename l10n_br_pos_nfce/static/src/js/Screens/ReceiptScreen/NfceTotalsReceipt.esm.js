/** @odoo-module */

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";

class NfceTotalsReceipt extends PosComponent {
    setup() {
        super.setup();

        this.order = this.props.receipt;
    }

    get totalOrderItemsLength() {
        return this.order.orderlines.length;
    }

    get totalOrderAmount() {
        return (this.order.total_with_tax || 0).toLocaleString("pt-BR", {
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

NfceTotalsReceipt.template = "NfceTotalsReceipt";

Registries.Component.add(NfceTotalsReceipt);
