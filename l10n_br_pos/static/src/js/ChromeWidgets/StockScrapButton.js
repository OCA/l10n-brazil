odoo.define("l10n_br_pos.StockScrapButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class StockScrapButton extends PosComponent {
        async onClick() {
            this.showPopup("StockScrapPopup", {});
        }
    }

    StockScrapButton.template = "StockScrapButton";
    Registries.Component.add(StockScrapButton);

    return StockScrapButton;
});
