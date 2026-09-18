/** @odoo-module */

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";

class NfceItemReceipt extends PosComponent {
    setup() {
        super.setup();

        this.line = this.props.line;
    }

    get id() {
        const lineCollections = this.env.pos.get_order().get_orderlines();

        const index =
            lineCollections.findIndex((line) => line.id === this.line.id) + 1;

        if (index < 100) {
            return String(index).padStart(3, "0");
        }

        return String(index);
    }

    get productCode() {
        return this.line.product_default_code || "";
    }

    get productName() {
        return this.line.product_name || "";
    }

    get productQuantityUnit() {
        const quantity = this.line.quantity || 0;
        const unit = this.line.unit_code || "";

        return `${quantity}${unit}`;
    }

    get productUnitValue() {
        return (this.line.price || 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    get productTotalValue() {
        return (this.line.price_without_tax || 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    get itemLine() {
        return [
            this.id,
            this.productCode,
            this.productName,
            `${this.productQuantityUnit} X ${this.productUnitValue}`,
            this.productTotalValue,
        ].join("\t");
    }
}

NfceItemReceipt.template = "NfceItemReceipt";

Registries.Component.add(NfceItemReceipt);