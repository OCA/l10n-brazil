/** @odoo-module */

import OrderReceipt from "point_of_sale.OrderReceipt";
import Registries from "point_of_sale.Registries";

class NFCeOrderReceipt extends OrderReceipt {
    setup() {
        super.setup();

        // console.log("### NFCeOrderReceipt SETUP ###");
    }

    get isHomologationEnvironment() {
        return this.receipt.nfce_environment === "2";
    }

    get hasChange() {
        return this.receipt.change;
    }

    get orderChange() {
        return this.receipt.change.toLocaleString("pt-br", {
            minimumFractionDigits: 2,
        });
    }
}

NFCeOrderReceipt.template = "NfceOrderReceipt";

Registries.Component.add(NFCeOrderReceipt);
