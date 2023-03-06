odoo.define("l10n_br_pos_nfce.NfceTotalsReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class NfceTotalsReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this.order = this.props.receipt;
        }

        get totalOrderItemsLength() {
            return this.order.orderlines.length;
        }

        get totalOrderAmount() {
            return this.order.total_with_tax.toLocaleString("pt-br", {
                minimumFractionDigits: 2,
            });
        }

        get totalOrderDiscount() {
            return this.order.total_discount.toLocaleString("pt-br", {
                minimumFractionDigits: 2,
            });
        }
    }
    NfceTotalsReceipt.template = "NfceTotalsReceipt";

    Registries.Component.add(NfceTotalsReceipt);

    return {NfceTotalsReceipt};
});
