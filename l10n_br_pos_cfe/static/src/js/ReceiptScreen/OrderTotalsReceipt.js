odoo.define("l10n_br_pos_cfe.OrderTotalsReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const utils = require("web.utils");

    const round_pr = utils.round_precision;

    class OrderTotalsReceipt extends PosComponent {
        get order() {
            return this.props.order;
        }

        get rounding() {
            return this.props.rounding;
        }

        // Getters //

        get total_with_tax() {
            return round_pr(this.order.total_with_tax, this.rounding).toFixed(2);
        }

        get total_discount() {
            return round_pr(this.order.total_discount, this.rounding).toFixed(2);
        }

        get subtotal() {
            return this.subtotal_without_discount(this.order.orderlines).toFixed(2);
        }

        subtotal_without_discount(orderlines) {
            return round_pr(
                orderlines.reduce((sum, line) => {
                    return sum + line.price * line.quantity;
                }, 0),
                this.rounding
            );
        }
    }
    OrderTotalsReceipt.template = "OrderTotalsReceipt";

    Registries.Component.add(OrderTotalsReceipt);

    return OrderTotalsReceipt;
});
