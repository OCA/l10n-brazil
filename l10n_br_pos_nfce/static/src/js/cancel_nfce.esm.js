import {PosStore} from "@point_of_sale/app/store/pos_store";
import {SelectionPopup} from "@point_of_sale/app/utils/input_popups/selection_popup";
import {TextInputPopup} from "@point_of_sale/app/utils/input_popups/text_input_popup";
import {_t} from "@web/core/l10n/translation";
import {makeAwaitable} from "@point_of_sale/app/store/make_awaitable_dialog";
import {patch} from "@web/core/utils/patch";

const OTHER_REASON = 999999;

patch(PosStore.prototype, {
    async _show_edit_reason_popup() {
        const reason = await makeAwaitable(this.dialog, TextInputPopup, {
            title: _t("Enter reason for cancellation!"),
        });

        return reason ? {id: OTHER_REASON, cancel_reason: reason} : false;
    },

    async _show_selection_popup() {
        const selected = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Reason for Cancellation?"),
            list: [
                {
                    id: 1,
                    item: {id: 1, cancel_reason: "Reason 1"},
                    label: "Reason 1",
                    isSelected: false,
                },
                {
                    id: OTHER_REASON,
                    item: {id: OTHER_REASON},
                    label: "Enter the reason",
                    isSelected: false,
                },
            ],
        });

        if (!selected) {
            return false;
        }

        if (selected.id === OTHER_REASON) {
            return (
                (await this._show_edit_reason_popup()) ||
                (await this._show_selection_popup())
            );
        }

        return selected;
    },

    async onDeleteOrder(order) {
        if (order && order.document_type === "65") {
            const cancelReason = await this._show_selection_popup();

            if (!cancelReason) {
                return false;
            }

            try {
                order.state_edoc = await this.data.call(
                    "pos.order",
                    "cancel_nfce_from_ui",
                    [order.pos_reference, cancelReason.cancel_reason]
                );
            } catch (error) {
                console.error("Error cancelling NFC-e:", error);
            }

            return false;
        }

        return super.onDeleteOrder(...arguments);
    },
});
