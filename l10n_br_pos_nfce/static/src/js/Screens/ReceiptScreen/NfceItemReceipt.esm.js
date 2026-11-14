import {Component} from "@odoo/owl";

export class NfceItemReceipt extends Component {
    static template = "l10n_br_pos_nfce.NfceItemReceipt";
    static props = {line: Object, index: Number};

    setup() {
        this.line = this.props.line;
    }

    get id() {
        const index = this.props.index + 1;

        if (index < 100) {
            return String(index).padStart(3, "0");
        }

        return String(index);
    }

    get productCode() {
        return this.line.product_default_code || "";
    }

    get productName() {
        return this.line.productName || "";
    }

    get productQuantityUnit() {
        const quantity = this.line.quantity || 0;
        const unit = this.line.unit_code || "";

        return `${quantity}${unit}`;
    }

    get productUnitValue() {
        return (this.line.unit_price || 0).toLocaleString("pt-BR", {
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
