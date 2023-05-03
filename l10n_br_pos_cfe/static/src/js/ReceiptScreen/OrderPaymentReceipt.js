odoo.define("l10n_br_pos_cfe.OrderPaymentReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const utils = require("web.utils");

    const round_pr = utils.round_precision;

    class OrderPaymentReceipt extends PosComponent {
        get paymentline() {
            return this.props.paymentline;
        }

        get rounding() {
            return this.props.rounding;
        }

        // Getters //

        get name() {
            return this.paymentline.name;
        }

        get amount() {
            return round_pr(this.paymentline.amount, this.rounding).toFixed(2);
        }
    }
    OrderPaymentReceipt.template = "OrderPaymentReceipt";

    Registries.Component.add(OrderPaymentReceipt);

    return OrderPaymentReceipt;
});
