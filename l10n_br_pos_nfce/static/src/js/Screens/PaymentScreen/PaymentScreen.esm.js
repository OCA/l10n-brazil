/** @odoo-module **/

import PaymentScreen from "point_of_sale.PaymentScreen";
import Registries from "point_of_sale.Registries";
import {_t} from "@web/core/l10n/translation";

const L10nBrPosNfcePaymentScreen = (OriginalPaymentScreen) =>
    class extends OriginalPaymentScreen {
        check_valid_cpf_cnpj(order) {
            const partner = order.get_partner();
            if (partner && partner.is_anonymous_consumer) {
                console.log("### CONSUMIDOR ANÔNIMO - BYPASS ###");
                return true;
            }

            return super.check_valid_cpf_cnpj(order);
        }

        async _isOrderValid() {
            const order = this.currentOrder;
            const partner = order.get_partner();
            if (
                order.is_detailed_invoice() &&
                partner &&
                partner.is_anonymous_consumer
            ) {
                this.showPopup("ErrorPopup", {
                    title: _t("Cliente não identificado"),
                    body: _t("Selecione um cliente identificado para emitir a NF-e."),
                });
                return false;
            }
            return super._isOrderValid(...arguments);
        }

        shouldDownloadInvoice() {
            if (this.env.pos.config.simplified_document_type === "65") {
                return false;
            }

            return super.shouldDownloadInvoice();
        }

        async _finalizeValidation() {
            if (this.env.pos.config.simplified_document_type === "65") {
                // O Odoo 16 chama push_single_order() sem opções; sem marcar o
                // pedido como faturado, o backend não cria a fatura/NFC-e e o
                // ReceiptScreen não usa o layout DANFE NFC-e.
                this.currentOrder.to_invoice = true;
            }

            return super._finalizeValidation(...arguments);
        }

        showScreen(screenName, props) {
            return super.showScreen(screenName, props);
        }

        get nextScreen() {
            if (this.env.pos.config.simplified_document_type === "65") {
                console.log("### NFCe -> ReceiptScreen ###");
                return "ReceiptScreen";
            }
            return super.nextScreen;
        }
    };
Registries.Component.extend(PaymentScreen, L10nBrPosNfcePaymentScreen);
