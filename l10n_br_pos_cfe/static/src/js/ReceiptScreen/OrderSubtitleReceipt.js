odoo.define("l10n_br_pos_cfe.OrderSubtitleReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class OrderSubtitleReceipt extends PosComponent {
        get order() {
            return this.props.receipt;
        }
    }
    OrderSubtitleReceipt.template = "OrderSubtitleReceipt";

    Registries.Component.add(OrderSubtitleReceipt);

    return OrderSubtitleReceipt;
});
