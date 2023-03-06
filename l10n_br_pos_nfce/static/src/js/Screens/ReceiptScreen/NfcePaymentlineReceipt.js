odoo.define("l10n_br_pos_nfce.NfcePaymentlineReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class NfcePaymentlineReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this.payment = this.props.payment;
        }

        get paymentName() {
            return this.payment.name;
        }

        get paymentAmount() {
            return this.payment.amount.toLocaleString("pt-br", {
                minimumFractionDigits: 2,
            });
        }
    }
    NfcePaymentlineReceipt.template = "NfcePaymentlineReceipt";

    Registries.Component.add(NfcePaymentlineReceipt);

    return {NfcePaymentlineReceipt};
});
