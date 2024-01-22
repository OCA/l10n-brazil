odoo.define("l10n_br_pos.CancelOrderButton", function (require) {
    "use strict";

    const {useListener} = require("web.custom_hooks");
    const {useContext} = owl.hooks;
    const PosComponent = require("point_of_sale.PosComponent");
    const OrderManagementScreen = require("point_of_sale.OrderManagementScreen");
    const Registries = require("point_of_sale.Registries");
    const contexts = require("point_of_sale.PosContext");

    class CancelOrderButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click", this._onClick);
            this.orderManagementContext = useContext(contexts.orderManagement);
        }

        async _show_edit_reason_popup(cancel_reason) {
            const {confirmed, payload} = await this.showPopup("TextInputPopup", {
                title: this.env._t("Enter reason for cancellation!"),
            });
            if (confirmed) {
                return {
                    id: cancel_reason.id,
                    notes: payload,
                };
            }
            return false;
        }

        async _show_selection_popup() {
            const cancel_reason_list = this.env.pos.cancel_reasons;
            let cancel_reason = null;
            const selectionList = [];

            for (let i = 0; i < cancel_reason_list.length; i++) {
                selectionList.push({
                    id: cancel_reason_list[i].id,
                    item: {
                        id: cancel_reason_list[i].id,
                        cancel_reason: cancel_reason_list[i].name,
                        is_custom: cancel_reason_list[i].is_custom,
                    },
                    label: cancel_reason_list[i].name,
                    isSelected: false,
                });
            }

            const {confirmed, payload} = await this.showPopup("SelectionPopup", {
                title: this.env._t("Reason for Cancellation?"),
                list: selectionList,
            });

            if (confirmed) {
                if (payload.is_custom) {
                    cancel_reason = await this._show_edit_reason_popup(payload);
                    if (!cancel_reason) {
                        cancel_reason = await this._show_selection_popup();
                    }
                } else {
                    cancel_reason = payload;
                }
            }
            return cancel_reason;
        }
        async _onClick() {
            const order = this.orderManagementContext.selectedOrder;

            if (!order) return;

            const cancel_reason = await this._show_selection_popup();

            if (cancel_reason) {
                const result = await order.document_cancel(cancel_reason);
                if (result) {
                    order.cancel_order(cancel_reason);
                    this.showScreen("ReprintReceiptScreen", {order: order});
                } else {
                    this.document_event_messages.push({
                        id: 5001,
                        label: "Cancellation failed.",
                    });
                }
            }
        }
    }
    CancelOrderButton.template = "CancelOrderButton";

    OrderManagementScreen.addControlButton({
        component: CancelOrderButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(CancelOrderButton);

    return CancelOrderButton;
});
