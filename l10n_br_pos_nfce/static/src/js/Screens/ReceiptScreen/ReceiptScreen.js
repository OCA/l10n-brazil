/** @odoo-module **/

import ReceiptScreen from "point_of_sale.ReceiptScreen";
import Registries from "point_of_sale.Registries";
import {useRef} from "@odoo/owl";


const L10nBrPosNfceReceiptScreen = (OriginalReceiptScreen) =>
    class extends OriginalReceiptScreen {
        setup() {
            super.setup();

            if (this.isNFCe()) {
                this.orderReceipt = useRef("nfce-order-receipt");
            } else {
                this.orderReceipt = useRef("order-receipt");
            }

        }

        isNFCe() {
            return (
                this.env.pos.config.simplified_document_type === "65" &&
                this.currentOrder.to_invoice
            );
        }
    };

Registries.Component.extend(ReceiptScreen, L10nBrPosNfceReceiptScreen);

