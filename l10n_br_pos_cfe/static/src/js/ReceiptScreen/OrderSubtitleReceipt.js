odoo.define("l10n_br_pos_cfe.OrderSubtitleReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class OrderSubtitleReceipt extends PosComponent {
        get order() {
            return this.props.order;
        }

        // Getters //

        get document_number() {
            return this.order.document_number || "";
        }

        get satAmbiente() {
            if (this.env.pos.config.sat_ambiente === "homologacao") {
                return true;
            }
            return false;
        }

        get isCanceled() {
            return this.order.state_edoc === "cancelada";
        }
    }
    OrderSubtitleReceipt.template = "OrderSubtitleReceipt";

    Registries.Component.add(OrderSubtitleReceipt);

    return OrderSubtitleReceipt;
});
