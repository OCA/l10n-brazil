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

        get sortedTemplates() {
            return this.sortObjects(this.template_by_id, "name");
        }

        get selectedTemplate() {
            const tmpl = Object.entries(this.sortedTemplates).find(
                ([, value]) => value.id === parseInt(this.state.productId)
            );

            return tmpl ? tmpl[1] : undefined;
        }

        get sortedVariants() {
            const self = this;

            var variants = {};
            this.selectedTemplate.product_variant_ids.forEach(function (variant_id) {
                variants[variant_id] = self.product_by_id[variant_id];
            });

            return this.sortObjects(variants, "display_name");
        }

        sortObjects(obj, field_name) {
            var sortable = [];
            for (var key in obj)
                if (obj.hasOwnProperty(key)) {
                    sortable.push([key, obj[key]]);
                }

            return sortable
                .sort(function (a, b) {
                    var x = a[1][field_name].toLowerCase(),
                        y = b[1][field_name].toLowerCase();

                    return x < y ? -1 : x > y ? 1 : 0;
                })
                .map((a) => a[1]);
        }

        validateFields() {
            if (
                !this.product_by_id[this.state.productVariantId] ||
                !this.state.productQty
            ) {
                return false;
            }

            return true;
        }

        prepareStockScrapVals() {
            const productVariant = this.product_by_id[this.state.productVariantId];

            return {
                product_id: productVariant.id,
                product_uom_id: productVariant.uom_id[0],
                scrap_qty: parseInt(this.state.productQty),
                reason_code_id: parseInt(this.state.scrapReasonId),
                location_id: this.env.pos.config.scrap_location_id[0],
                scrap_location_id: this.env.pos.config.scrap_source_location_id[0],
            };
        }

        async createStockScrap() {
            if (!this.validateFields()) {
                $(".error-msg").show();
                return;
            }

            await rpc.query({
                model: "stock.scrap",
                method: "create",
                args: [this.prepareStockScrapVals()],
            });

            this.cancel();
        }
    }

    StockScrapPopup.template = "StockScrapPopup";
    Registries.Component.add(StockScrapPopup);

    return StockScrapPopup;
});
