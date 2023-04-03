odoo.define("l10n_br_pos_cfe.CancelOrderButton", function (require) {
    "use strict";

    const rpc = require("web.rpc");
    const CancelOrderButton = require("l10n_br_pos.CancelOrderButton");
    const Registries = require("point_of_sale.Registries");

    const L10nBrPosNFCeCancelOrderButton = (CancelOrderButton) =>
        class extends CancelOrderButton {
            async _onClick() {
                const currentOrder = this.orderManagementContext.selectedOrder;

                if (!currentOrder) return;

                if (currentOrder.document_type !== "65") {
                    super._onClick(...arguments);
                    return;
                }

                const cancelReason = await this._show_selection_popup();

                if (!cancelReason) return;

                try {
                    const result = await rpc.query({
                        model: "pos.order",
                        method: "cancel_nfce_from_ui",
                        args: [{}, currentOrder.name, cancelReason.cancel_reason],
                    });
                    currentOrder.state_edoc = result;
                } catch (error) {
                    console.error(
                        "l10n_br_pos_nfce ~ file: CancelOrderButton.js:32 ~ error:",
                        error
                    );
                    throw error;
                }
            }
        };

    Registries.Component.extend(CancelOrderButton, L10nBrPosNFCeCancelOrderButton);

    return L10nBrPosNFCeCancelOrderButton;
});
