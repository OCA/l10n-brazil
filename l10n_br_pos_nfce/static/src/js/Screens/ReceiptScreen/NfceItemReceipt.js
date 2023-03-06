odoo.define("l10n_br_pos_nfce.NfceItemReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class NfceItemReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this.line = this.props.line;
        }

        get id() {
            const lineCollections = this.env.pos.get_order().get_orderlines();
            const index = _.findIndex(lineCollections, {id: this.line.id}) + 1;
            if (index < 100) {
                return String(index).padStart(3, "0");
            }
            return String(index);
        }

        get productCode() {
            return this.line.product_default_code;
        }

        get productName() {
            return this.line.product_name;
        }

        get productQuantityUnit() {
            return `${this.line.quantity}${this.line.unit_code}`;
        }

        get productUnitValue() {
            return this.line.price.toLocaleString("pt-br", {minimumFractionDigits: 2});
        }

        get productTotalValue() {
            return this.line.price_without_tax.toLocaleString("pt-br", {
                minimumFractionDigits: 2,
            });
        }

        get itemLine() {
            const id = this.id;
            const productCode = this.productCode;
            const productName = this.productName;
            const productQuantityUnit = this.productQuantityUnit;
            const productUnitValue = this.productUnitValue;
            const productTotalValue = this.productTotalValue;
            return `${id}\t${productCode}\t${productName}\t${productQuantityUnit} X ${productUnitValue}\t${productTotalValue}`;
        }
    }
    NfceItemReceipt.template = "NfceItemReceipt";

    Registries.Component.add(NfceItemReceipt);

    return {NfceItemReceipt};
});
