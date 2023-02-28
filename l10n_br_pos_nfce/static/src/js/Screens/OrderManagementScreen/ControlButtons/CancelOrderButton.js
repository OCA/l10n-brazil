odoo.define("l10n_br_pos_cfe.CancelOrderButton", function (require) {
    "use strict";

    const rpc = require("web.rpc");
    const CancelOrderButton = require("l10n_br_pos.CancelOrderButton");
    const Registries = require("point_of_sale.Registries");

    const L10nBrPosNFCeCancelOrderButton = (CancelOrderButton) =>
        class extends CancelOrderButton {
            /**
             * @override
             */
            async _onClick() {
                const currentOrder = this.orderManagementContext.selectedOrder;
                if (!currentOrder) return;
                const cancelReason = await this._show_selection_popup();
                if (cancelReason) {
                    try {
                        rpc.query({
                            model: "pos.order",
                            method: "cancel_nfce_from_ui",
                            args: [{}, currentOrder.name, cancelReason.cancel_reason],
                        }).then(function (result) {
                            currentOrder.state_edoc = result;
                        });
                    } catch (error) {
                        throw error;
                    }
                }
            }
        };

    Registries.Component.extend(CancelOrderButton, L10nBrPosNFCeCancelOrderButton);

    return L10nBrPosNFCeCancelOrderButton;
});
