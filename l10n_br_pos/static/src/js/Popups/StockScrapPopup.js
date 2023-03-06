odoo.define("l10n_br_pos.StockScrapPopup", function (require) {
    "use strict";

    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const Registries = require("point_of_sale.Registries");
    const {useState} = owl.hooks;
    const rpc = require("web.rpc");

    class StockScrapPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);

            this.state = useState({});
            this.product_by_id = this.env.pos.db.product_by_id;
            this.template_by_id = this.env.pos.db.template_by_id;
        }

        get sorted_templates() {
            return this.sortObject(this.template_by_id, "name");
        }

        get selected_template() {
            const tmpl = Object.entries(this.sorted_templates).find(
                ([, value]) => value.id === parseInt(this.state.productId)
            );

            return tmpl ? tmpl[1] : false;
        }

        get variants() {
            return this.selected_template.product_variant_ids;
        }

        sortObject(obj, field) {
            var sortable = [];
            for (var key in obj)
                if (obj.hasOwnProperty(key)) sortable.push([key, obj[key]]);

            sortable.sort(function (a, b) {
                var x = a[1][field].toLowerCase(),
                    y = b[1][field].toLowerCase();

                return x < y ? -1 : x > y ? 1 : 0;
            });
            return sortable.map((a) => a[1]);
        }

        async createStockScrap() {
            const scrapQty = this.state.productQty;
            const scrapReasonId = this.state.scrapReasonId;
            const sourceLocationId = this.env.pos.config.scrap_source_location_id[0];
            const locationId = this.env.pos.config.scrap_location_id[0];
            const productVariant = this.product_by_id[this.state.productVariantId];

            if (!productVariant || !scrapQty) {
                return await this.showPopup("ErrorPopup", {
                    title: this.env._t("Missing Data"),
                    body: this.env._t("Please fill all the necessary data to proceed."),
                });
            }

            await rpc.query({
                model: "stock.scrap",
                method: "create",
                args: [
                    {
                        product_id: productVariant.id,
                        product_uom_id: productVariant.uom_id[0],
                        scrap_qty: parseInt(scrapQty),
                        reason_code_id: parseInt(scrapReasonId),
                        location_id: locationId,
                        scrap_location_id: sourceLocationId,
                    },
                ],
            });

            this.cancel();
        }
    }

    StockScrapPopup.template = "StockScrapPopup";
    Registries.Component.add(StockScrapPopup);

    return StockScrapPopup;
});
