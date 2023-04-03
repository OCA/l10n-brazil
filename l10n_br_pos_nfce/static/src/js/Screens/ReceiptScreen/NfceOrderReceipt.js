odoo.define("l10n_br_pos_nfce.NfceOrderReceipt", function (require) {
    "use strict";

    const OrderReceipt = require("point_of_sale.OrderReceipt");
    const Registries = require("point_of_sale.Registries");

    class NFCeOrderReceipt extends OrderReceipt {
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

    Registries.Component.add(NFCeOrderReceipt);
    NFCeOrderReceipt.template = "NfceOrderReceipt";

    return NFCeOrderReceipt;
});
