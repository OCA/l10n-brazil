odoo.define("l10n_br_pos.StockScrapPopup", function (require) {
    "use strict";

    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const Registries = require("point_of_sale.Registries");
    const {useState} = owl.hooks;
    const rpc = require("web.rpc");

    class StockScrapPopup extends AbstractAwaitablePopup {
        setup() {
            this.state = useState({});
            this.product_by_id = this.env.pos.db.product_by_id;
            this.template_by_id = this.env.pos.db.template_by_id;

            this.setupProductTable();
        }

        setupProductTable() {
            const self = this;

            $(document).ready(() => $(".scrap-product-table").DataTable());
            $(document).on("click", ".scrap-product-table td", (ev) =>
                self._selectProduct(ev)
            );
        }

        _selectProduct(event) {
            const $target = $(event.currentTarget);
            $("td").removeClass("highlighted");
            $target.addClass("highlighted");

            this.state.productId = $target.attr("value");
        }

        get templates() {
            return Object.entries(this.template_by_id).map((a) => a[1]);
        }

        get selectedTemplate() {
            return this.templates.find(
                (value) => value.id === parseInt(this.state.productId)
            );
        }

        get variants() {
            return this.selectedTemplate.product_variant_ids.map(
                (a) => this.product_by_id[a]
            );
        }

        get selectedVariant() {
            return this.product_by_id[this.state.productVariantId];
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
                !this.selectedVariant ||
                !this.state.productQty ||
                !this.state.scrapReasonId
            ) {
                return false;
            }

            return true;
        }

        prepareStockScrapVals() {
            return {
                product_id: this.selectedVariant.id,
                product_uom_id: this.selectedVariant.uom_id[0],
                scrap_qty: parseFloat(this.state.productQty),
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
                method: "create_and_do_scrap",
                args: [this.prepareStockScrapVals()],
            });

            this.cancel();
        }
    }

    StockScrapPopup.template = "StockScrapPopup";
    Registries.Component.add(StockScrapPopup);

    return StockScrapPopup;
});
