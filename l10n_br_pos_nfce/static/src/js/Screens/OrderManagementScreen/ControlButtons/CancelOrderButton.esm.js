/** @odoo-module **/

import {SelectionPopup} from "@point_of_sale/app/utils/input_popups/selection_popup";
import {TextInputPopup} from "@point_of_sale/app/utils/input_popups/text_input_popup";
import {TicketScreen} from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

patch(TicketScreen.prototype, {
    async _show_edit_reason_popup() {
        const {confirmed, payload} = await this.popup.add(TextInputPopup, {
            title: _t("Enter reason for cancellation!"),
        });

        if (confirmed) {
            return {
                id: 999999,
                cancel_reason: payload,
            };
        }

        return false;
    },

    async _show_selection_popup() {
        let cancel_reason = null;

        const selectionList = [
            {
                id: 1,
                item: {
                    id: 1,
                    cancel_reason: "Reason 1",
                },
                label: "Reason 1",
                isSelected: false,
            },
            {
                id: 999999,
                item: {
                    id: 999999,
                },
                label: "Enter the reason",
                isSelected: false,
            },
        ];

        const {confirmed, payload} = await this.popup.add(SelectionPopup, {
            title: _t("Reason for Cancellation?"),
            list: selectionList,
        });

        if (!confirmed) {
            return false;
        }

        if (payload.id === 999999) {
            cancel_reason = await this._show_edit_reason_popup();

            if (!cancel_reason) {
                cancel_reason = await this._show_selection_popup();
            }
        } else {
            cancel_reason = payload;
        }

        return cancel_reason;
    },

    async onDeleteOrder(order) {
        if (order && order.document_type === "65") {
            const cancelReason = await this._show_selection_popup();

            if (!cancelReason) {
                return;
            }

            try {
                const result = await this.orm.call("pos.order", "cancel_nfce_from_ui", [
                    {},
                    order.name,
                    cancelReason.cancel_reason,
                ]);

                order.state_edoc = result;
            } catch (error) {
                console.error("Error cancelling NFC-e:", error);
            }

            return;
        }

        return super.onDeleteOrder(...arguments);
    },
});
