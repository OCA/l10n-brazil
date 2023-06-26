odoo.define("l10n_br_pos_cfe.SatOrderReceipt", function (require) {
    "use strict";

    const OrderReceipt = require("point_of_sale.OrderReceipt");
    const Registries = require("point_of_sale.Registries");

    const utils = require("web.utils");

    const round_pr = utils.round_precision;

    const SatOrderReceipt = (OrderReceipt_screen = OrderReceipt) =>
        class extends OrderReceipt_screen {
            get isCanceled() {
                return this.props.order.state_edoc === "cancelada";
            }

            get total() {
                return round_pr(
                    this.props.order.get_total_with_tax(),
                    this.rounding
                ).toFixed(2);
            }
        };

    Registries.Component.extend(OrderReceipt, SatOrderReceipt);
    /*
     * Overwrite the original component template, as it is giving OWL
     * error when we try to inherit and change the information from
     * the entire original template.
     */
    OrderReceipt.template = "SatOrderReceipt";

    return OrderReceipt;
});
