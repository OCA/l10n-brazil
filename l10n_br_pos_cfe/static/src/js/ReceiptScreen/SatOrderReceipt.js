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

            get est_state_tax_total() {
                let state_tax = 0;
                const lines = this.props.order.get_orderlines();
                for (var i = 0, len = lines.length; i < len; i++) {
                    const line_price = lines[i].price * lines[i].quantity;
                    const product_tmpl_id = lines[i].product.product_tmpl_id;
                    const map = this.props.order.pos.fiscal_map_by_template_id[
                        product_tmpl_id
                    ];

                    state_tax += (line_price * map.icms_percent) / 100;
                }

                return state_tax;
            }

            get est_federal_tax_total() {
                let federal_tax = 0;
                const lines = this.props.order.get_orderlines();
                for (var i = 0, len = lines.length; i < len; i++) {
                    const line_price = lines[i].price * lines[i].quantity;
                    const product_tmpl_id = lines[i].product.product_tmpl_id;
                    const map = this.props.order.pos.fiscal_map_by_template_id[
                        product_tmpl_id
                    ];

                    federal_tax += (line_price * map.pis_percent) / 100;
                    federal_tax += (line_price * map.cofins_percent) / 100;
                }

                return federal_tax;
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
