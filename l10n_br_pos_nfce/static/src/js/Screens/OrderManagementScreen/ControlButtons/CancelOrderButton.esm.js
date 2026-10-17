/** @odoo-module **/

import TicketScreen from "point_of_sale.TicketScreen";
import Registries from "point_of_sale.Registries";

const L10nBrPosNFCeTicketScreen = (OriginalTicketScreen) =>
    class extends OriginalTicketScreen {
        async _show_edit_reason_popup() {
            const {confirmed, payload} = await this.showPopup("TextInputPopup", {
                title: this.env._t("Enter reason for cancellation!"),
            });

            if (confirmed) {
                return {
                    id: 999999,
                    cancel_reason: payload,
                };
            }

            return false;
        }

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

            const {confirmed, payload} = await this.showPopup("SelectionPopup", {
                title: this.env._t("Reason for Cancellation?"),
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
        }

        async _onDeleteOrder({detail: order}) {
            if (order && order.document_type === "65") {
                const cancelReason = await this._show_selection_popup();

                if (!cancelReason) {
                    return;
                }

                try {
                    const result = await this.rpc({
                        model: "pos.order",
                        method: "cancel_nfce_from_ui",
                        args: [{}, order.name, cancelReason.cancel_reason],
                    });

                    order.state_edoc = result;

                    return;
                } catch (error) {
                    console.error("Erro ao cancelar NFC-e:", error);

                    return;
                }
            }

            return super._onDeleteOrder(...arguments);
        }
    };

Registries.Component.extend(TicketScreen, L10nBrPosNFCeTicketScreen);
