/** @odoo-module **/

import PaymentScreen from "point_of_sale.PaymentScreen";
import Registries from "point_of_sale.Registries";

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

        shouldDownloadInvoice() {
            if (this.env.pos.config.simplified_document_type === "65") {
                return false;
            }

            return super.shouldDownloadInvoice();
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
